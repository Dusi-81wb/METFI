"""Candidate generation and multi-source record linkage for financial reconciliation."""

import hashlib
from collections import defaultdict

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
    CanonicalTransactionGroup,
)
from app.domain.time import hours_between


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two reference strings."""
    if s1 == s2:
        return 0
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class CandidateMatcher:
    """
    High-speed, deterministic candidate grouping engine.

    Uses hash indexing on payment_id and order_id to achieve O(N) grouping,
    with customer-guarded fuzzy candidate resolution and multi-candidate ambiguity detection.
    """

    def group_candidates(
        self,
        payments: list[CanonicalPayment],
        settlements: list[CanonicalSettlement],
        ledger_entries: list[CanonicalLedgerEntry],
    ) -> list[CanonicalTransactionGroup]:
        """
        Group tri-source records into unified canonical transaction groups.

        Guarantees:
        - Deterministic grouping and stable ordering.
        - Strict customer isolation (no cross-customer linking).
        - Multi-candidate ambiguity detection for ties.
        - Full multi-settlement tracking and fuzzy settlement linkage.
        """
        # 1. Index settlements by payment_id
        settlements_by_payment_id: dict[str, list[CanonicalSettlement]] = defaultdict(list)
        for s in settlements:
            settlements_by_payment_id[s.payment_id].append(s)

        # 2. Index ledger entries by order_id
        ledger_by_order_id: dict[str, list[CanonicalLedgerEntry]] = defaultdict(list)
        for le in ledger_entries:
            ledger_by_order_id[le.order_id].append(le)

        used_payment_ids: set[str] = set()
        used_settlement_ids: set[str] = set()
        used_ledger_order_ids: set[str] = set()

        groups: list[CanonicalTransactionGroup] = []

        # 3. Primary pass: Group around known Payments (Exact reference match)
        unlinked_payments: list[CanonicalPayment] = []
        payments_with_missing_settlement: list[
            tuple[CanonicalPayment, list[CanonicalLedgerEntry], bool]
        ] = []

        for p in payments:
            used_payment_ids.add(p.payment_id)
            matched_settlements = list(settlements_by_payment_id.get(p.payment_id, []))
            for s in matched_settlements:
                used_settlement_ids.add(s.settlement_id)

            if p.order_id in ledger_by_order_id:
                matched_ledger = ledger_by_order_id[p.order_id]
                used_ledger_order_ids.add(p.order_id)

                # Customer consistency check on ledger metadata
                is_cross_customer = False
                for le in matched_ledger:
                    led_cust = le.metadata.get("customer_id")
                    if led_cust and p.customer_id and led_cust != p.customer_id:
                        is_cross_customer = True
                        break

                if matched_settlements:
                    case_id = self._generate_case_id(p.order_id, p.payment_id)
                    groups.append(
                        CanonicalTransactionGroup(
                            case_id=case_id,
                            order_id=p.order_id,
                            payment=p,
                            settlement=matched_settlements[0],
                            settlements=matched_settlements,
                            ledger_entries=matched_ledger,
                            is_cross_customer_rejected=is_cross_customer,
                        )
                    )
                else:
                    payments_with_missing_settlement.append((p, matched_ledger, is_cross_customer))
            else:
                unlinked_payments.append(p)

        # 4. Secondary pass: Resolve unlinked settlements for payments
        unlinked_settlements = [
            s for s in settlements if s.settlement_id not in used_settlement_ids
        ]
        unlinked_ledger_orders = [
            order_id for order_id in ledger_by_order_id if order_id not in used_ledger_order_ids
        ]

        # 4a. Check unlinked settlements for payments that matched ledger
        for p, matched_ledger, is_cross_customer in payments_with_missing_settlement:
            resolved_settlements: list[CanonicalSettlement] = []
            for s in unlinked_settlements:
                if s.settlement_id in used_settlement_ids:
                    continue
                if s.currency != p.currency:
                    continue
                if abs(len(s.payment_id) - len(p.payment_id)) > 3:
                    continue
                time_diff = abs(hours_between(p.payment_timestamp, s.settlement_timestamp))
                if time_diff > 72.0:
                    continue
                if _levenshtein_distance(p.payment_id, s.payment_id) <= 3:
                    resolved_settlements.append(s)
                    used_settlement_ids.add(s.settlement_id)
                    break

            case_id = self._generate_case_id(p.order_id, p.payment_id)
            primary_settlement = resolved_settlements[0] if resolved_settlements else None
            groups.append(
                CanonicalTransactionGroup(
                    case_id=case_id,
                    order_id=p.order_id,
                    payment=p,
                    settlement=primary_settlement,
                    settlements=resolved_settlements,
                    ledger_entries=matched_ledger,
                    is_cross_customer_rejected=is_cross_customer,
                )
            )

        # 4b. Fuzzy matching for unlinked payments
        for p in unlinked_payments:
            fuzzy_settlements = list(settlements_by_payment_id.get(p.payment_id, []))
            for s in fuzzy_settlements:
                used_settlement_ids.add(s.settlement_id)

            if not fuzzy_settlements:
                for s in unlinked_settlements:
                    if s.settlement_id in used_settlement_ids:
                        continue
                    if s.currency != p.currency:
                        continue
                    if abs(len(s.payment_id) - len(p.payment_id)) > 3:
                        continue
                    time_diff = abs(hours_between(p.payment_timestamp, s.settlement_timestamp))
                    if time_diff > 72.0:
                        continue
                    if _levenshtein_distance(p.payment_id, s.payment_id) <= 3:
                        fuzzy_settlements.append(s)
                        used_settlement_ids.add(s.settlement_id)
                        break

            candidate_orders: list[tuple[str, int]] = []
            cross_customer_attempt = False

            for led_order in unlinked_ledger_orders:
                if led_order in used_ledger_order_ids:
                    continue
                entries = ledger_by_order_id[led_order]
                if not entries:
                    continue

                if entries[0].currency != p.currency:
                    continue

                # Monetary compatibility
                has_matching_amount = any(
                    le.debit == p.amount or le.credit == p.amount for le in entries
                )
                if not has_matching_amount:
                    continue

                time_diff = abs(hours_between(p.payment_timestamp, entries[0].entry_timestamp))
                if time_diff > 2.0:
                    continue

                if abs(len(p.order_id) - len(led_order)) > 3:
                    continue

                dist = _levenshtein_distance(p.order_id, led_order)
                if dist > 3:
                    continue

                customer_mismatch = False
                for le in entries:
                    led_cust = le.metadata.get("customer_id")
                    if led_cust and p.customer_id and led_cust != p.customer_id:
                        customer_mismatch = True
                        break

                if customer_mismatch:
                    cross_customer_attempt = True
                    continue

                candidate_orders.append((led_order, dist))

            matched_ledger = []
            is_ambiguous = False

            if candidate_orders:
                candidate_orders.sort(key=lambda x: (x[1], x[0]))
                min_dist = candidate_orders[0][1]
                best_candidates = [co[0] for co in candidate_orders if co[1] == min_dist]

                if len(best_candidates) == 1:
                    selected_order = best_candidates[0]
                    matched_ledger = ledger_by_order_id[selected_order]
                    used_ledger_order_ids.add(selected_order)
                else:
                    is_ambiguous = True

            case_id = self._generate_case_id(p.order_id, p.payment_id)
            primary_settlement = fuzzy_settlements[0] if fuzzy_settlements else None
            groups.append(
                CanonicalTransactionGroup(
                    case_id=case_id,
                    order_id=p.order_id,
                    payment=p,
                    settlement=primary_settlement,
                    settlements=fuzzy_settlements,
                    ledger_entries=matched_ledger,
                    is_ambiguous_candidate=is_ambiguous,
                    is_cross_customer_rejected=cross_customer_attempt,
                )
            )

        # 5. Tertiary pass: Orphaned settlements
        for s in settlements:
            if s.settlement_id not in used_settlement_ids:
                used_settlement_ids.add(s.settlement_id)
                case_id = f"case_orph_set_{s.settlement_id}"
                groups.append(
                    CanonicalTransactionGroup(
                        case_id=case_id,
                        order_id=f"UNKNOWN_{s.settlement_id}",
                        payment=None,
                        settlement=s,
                        settlements=[s],
                        ledger_entries=[],
                    )
                )

        # 6. Quaternary pass: Orphaned ledger entries
        for led_order in ledger_by_order_id:
            if led_order not in used_ledger_order_ids:
                used_ledger_order_ids.add(led_order)
                entries = ledger_by_order_id[led_order]
                case_id = f"case_orph_led_{led_order}"
                groups.append(
                    CanonicalTransactionGroup(
                        case_id=case_id,
                        order_id=led_order,
                        payment=None,
                        settlement=None,
                        settlements=[],
                        ledger_entries=entries,
                    )
                )

        # Sort groups deterministically by case_id for perfectly stable execution order
        groups.sort(key=lambda g: g.case_id)
        return groups

    def _generate_case_id(self, order_id: str, payment_id: str) -> str:
        """Deterministically derive a case identifier from primary record identifiers."""
        key = f"case:{order_id}:{payment_id}".encode()
        digest = hashlib.sha256(key).hexdigest()[:12]
        return f"case_{digest}"
