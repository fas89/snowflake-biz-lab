select
  account_id,
  service_id,
  count_if(status <> 'resolved') as open_ticket_count_30d,
  avg(
    case severity
      when 'critical' then 4
      when 'high' then 3
      when 'medium' then 2
      else 1
    end
  ) as ticket_severity_index,
  current_timestamp() as snapshot_at
from {{ source('telco_stage', 'trouble_ticket') }}
where opened_at >= dateadd(day, -30, current_timestamp())
group by account_id, service_id
