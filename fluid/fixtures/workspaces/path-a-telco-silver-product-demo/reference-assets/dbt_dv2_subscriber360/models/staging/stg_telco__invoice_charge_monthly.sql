select
  svc.account_id,
  sub.service_id,
  round(sum(ic.amount_chf), 2) as total_charges_30d,
  round(sum(case when ic.charge_type = 'recurring_charge' then ic.amount_chf else 0 end), 2) as monthly_recurring_charge,
  current_timestamp() as snapshot_at
from {{ source('telco_stage', 'invoice_charge') }} ic
join {{ source('telco_stage', 'invoice') }} inv
  on ic.invoice_id = inv.invoice_id
join {{ source('telco_stage', 'service') }} svc
  on inv.account_id = svc.account_id
join {{ source('telco_stage', 'subscription') }} sub
  on svc.service_id = sub.service_id
where ic.charge_date >= dateadd(day, -30, current_date())
group by svc.account_id, sub.service_id
