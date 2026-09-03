/**
 * TypeScript types for Microsoft Purview-style Rule Studio.
 */

export type RuleField =
  | 'monetary.fee_variance'
  | 'monetary.tax_variance'
  | 'monetary.settlement_amount_delta'
  | 'monetary.payment_gross'
  | 'monetary.settled_net'
  | 'timing.hours_to_settlement'
  | 'currency.payment_currency'
  | 'cardinality.settlement_count';

export type RuleOperator = '<=' | '>=' | '==' | '!=' | '<' | '>';

export type RuleType = 'CLASSIFICATION' | 'POLICY_GATE';

export interface RuleCondition {
  field: RuleField;
  operator: RuleOperator;
  value: number | string;
  secondary_field?: RuleField | null;
  secondary_operator?: RuleOperator | null;
  secondary_value?: number | string | null;
}

export interface CustomRule {
  rule_id: string;
  name: string;
  description: string;
  rule_type: RuleType;
  condition: RuleCondition;
  target_classification: string;
  target_policy_outcome: string;
  priority: number;
  is_enabled: boolean;
  is_system: boolean;
  created_at: string;
}

export interface CreateRuleRequest {
  name: string;
  description: string;
  rule_type: RuleType;
  condition: RuleCondition;
  target_classification: string;
  target_policy_outcome: string;
  priority: number;
  is_enabled: boolean;
}

export interface ToggleRuleRequest {
  is_enabled: boolean;
}
