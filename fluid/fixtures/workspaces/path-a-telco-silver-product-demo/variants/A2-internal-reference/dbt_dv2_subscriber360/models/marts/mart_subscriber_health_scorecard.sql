{{ config(alias='SUBSCRIBER_HEALTH_SCORECARD_V1') }}
select
  account_id,
  service_id,
  usage_events_30d,
  data_mb_30d,
  interaction_count_30d,
  open_ticket_count_30d,
  ticket_severity_index,
  total_charges_30d,
  monthly_recurring_charge,
  support_health_score,
  support_risk_band,
  snapshot_at
from {{ ref('sat_service_support_health') }}
