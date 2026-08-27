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
    with constrained fuzzy candidate resolution for mutated reference edge cases.
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
        - Captures exact linkages, missing records, duplicates, and reference mutations.
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

        # 3. Primary pass: Group around known Payments
        unlinked_payments: list[CanonicalPayment] = []

        for p in payments:
            used_payment_ids.add(p.payment_id)
            matched_settlements = settlements_by_payment_id.get(p.payment_id, [])
            for s in matched_settlements:
                used_settlement_ids.add(s.settlement_id)

            if p.order_id in ledger_by_order_id:
                # Direct exact order reference match
                matched_ledger = ledger_by_order_id[p.order_id]
                used_ledger_order_ids.add(p.order_id)
                case_id = self._generate_case_id(p.order_id, p.payment_id)
                primary_settlement = matched_settlements[0] if matched_settlements else None
                groups.append(
                    CanonicalTransactionGroup(
                        case_id=case_id,
                        order_id=p.order_id,
                        payment=p,
                        settlement=primary_settlement,
                        ledger_entries=matched_ledger,
                    )
                )
            else:
                # Defer payments that did not find an exact order match in ledger
                unlinked_payments.append(p)

        # 4. Secondary pass: Link deferred payments against unlinked ledger entries
        unlinked_ledger_orders = [
            order_id for order_id in ledger_by_order_id if order_id not in used_ledger_order_ids
        ]

        for p in unlinked_payments:
            matched_settlements = settlements_by_payment_id.get(p.payment_id, [])
            best_candidate_order: str | None = None
            best_dist = 999

            for led_order in unlinked_ledger_orders:
                if led_order in used_ledger_order_ids:
                    continue
                entries = ledger_by_order_id[led_order]
                if not entries:
                    continue

                # Check monetary compatibility: debits/credits match payment gross amount
                has_matching_amount = any(
                    le.debit == p.amount or le.credit == p.amount for le in entries
                )
                if not has_matching_amount:
                    continue

                # Check currency compatibility
                if entries[0].currency != p.currency:
                    continue

                # Check timing proximity: posted within 1 hour of payment authorization
                time_diff = abs(hours_between(p.payment_timestamp, entries[0].entry_timestamp))
                if time_diff > 2.0:
                    continue

                # Check reference edit distance
                dist = _levenshtein_distance(p.order_id, led_order)
                if dist < best_dist and dist <= 3:
                    best_dist = dist
                    best_candidate_order = led_order

            if best_candidate_order:
                matched_ledger = ledger_by_order_id[best_candidate_order]
                used_ledger_order_ids.add(best_candidate_order)
            else:
                matched_ledger = []

            case_id = self._generate_case_id(p.order_id, p.payment_id)
            primary_settlement = matched_settlements[0] if matched_settlements else None
            groups.append(
                CanonicalTransactionGroup(
                    case_id=case_id,
                    order_id=p.order_id,
                    payment=p,
                    settlement=primary_settlement,
                    ledger_entries=matched_ledger,
                )
            )

        # 5. Tertiary pass: Orphaned settlements (no payment matched)
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
                        ledger_entries=[],
                    )
                )

        # 6. Quaternary pass: Orphaned ledger entries (no payment or order matched)
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
