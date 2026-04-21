select
  s.hk_service,
  s.account_id,
  s.service_id,
  s.service_status,
  coalesce(u.usage_events_30d, 0) as usage_events_30d,
  coalesce(u.data_mb_30d, 0) as data_mb_30d,
  coalesce(i.interaction_count_30d, 0) as interaction_count_30d,
  i.last_interaction_at,
  coalesce(t.open_ticket_count_30d, 0) as open_ticket_count_30d,
  coalesce(t.ticket_severity_index, 0) as ticket_severity_index,
  coalesce(c.total_charges_30d, 0) as total_charges_30d,
  coalesce(c.monthly_recurring_charge, 0) as monthly_recurring_charge,
  greatest(
    s.load_dts,
    coalesce(u.snapshot_at, s.load_dts),
    coalesce(i.snapshot_at, s.load_dts),
    coalesce(t.snapshot_at, s.load_dts),
    coalesce(c.snapshot_at, s.load_dts)
  ) as snapshot_at,
  case
    when coalesce(t.open_ticket_count_30d, 0) >= 3 then 'critical'
    when coalesce(i.interaction_count_30d, 0) >= 5 then 'high'
    when coalesce(u.data_mb_30d, 0) = 0 and s.service_status = 'active' then 'watch'
    else 'healthy'
  end as support_risk_band,
  round(
    100
    - least(coalesce(t.open_ticket_count_30d, 0) * 12, 36)
    - least(coalesce(i.interaction_count_30d, 0) * 5, 25)
    + least(coalesce(c.monthly_recurring_charge, 0) / 8, 15),
    2
  ) as support_health_score,
  {{ dv2_hashdiff(["s.service_status", "u.usage_events_30d", "u.data_mb_30d", "i.interaction_count_30d", "t.open_ticket_count_30d", "t.ticket_severity_index", "c.total_charges_30d", "c.monthly_recurring_charge"]) }} as hashdiff,
  current_timestamp() as load_dts,
  'TELCO_DV2.SAT_SERVICE_SUPPORT_HEALTH' as record_source
from {{ ref('stg_telco__service') }} s
left join {{ ref('stg_telco__usage_event_daily') }} u
  on s.service_id = u.service_id
left join {{ ref('stg_telco__customer_interaction_daily') }} i
  on s.account_id = i.account_id
  and coalesce(s.service_id, '') = coalesce(i.service_id, s.service_id)
left join {{ ref('stg_telco__trouble_ticket_status') }} t
  on s.account_id = t.account_id
  and coalesce(s.service_id, '') = coalesce(t.service_id, s.service_id)
left join {{ ref('stg_telco__invoice_charge_monthly') }} c
  on s.account_id = c.account_id
  and s.service_id = c.service_id
