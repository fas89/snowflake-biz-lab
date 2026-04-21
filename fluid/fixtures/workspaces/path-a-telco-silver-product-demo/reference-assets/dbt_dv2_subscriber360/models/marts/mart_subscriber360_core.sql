{{ config(alias='SUBSCRIBER360_CORE_V1') }}
select
  p.party_id,
  a.account_id,
  a.account_number,
  s.service_id,
  sub.subscription_id,
  po.product_offering_name,
  s.service_status,
  a.account_status as billing_status,
  h.monthly_recurring_charge,
  h.data_mb_30d,
  h.interaction_count_30d,
  h.open_ticket_count_30d,
  h.support_health_score,
  h.support_risk_band,
  h.last_interaction_at,
  h.snapshot_at
from {{ ref('sat_account_profile') }} a
join {{ ref('stg_telco__service') }} s
  on a.account_id = s.account_id
left join {{ ref('stg_telco__subscription') }} sub
  on s.service_id = sub.service_id
left join {{ ref('stg_telco__product_offering') }} po
  on sub.product_offering_id = po.product_offering_id
left join {{ ref('sat_service_support_health') }} h
  on s.hk_service = h.hk_service
left join {{ ref('stg_telco__account') }} p
  on a.account_id = p.account_id
