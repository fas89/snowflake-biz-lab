select
  service_id,
  account_id,
  count(*) as usage_events_30d,
  round(sum(case when usage_type = 'data_mb' then quantity else 0 end), 2) as data_mb_30d,
  round(sum(case when usage_type = 'voice_min' then quantity else 0 end), 2) as voice_min_30d,
  current_timestamp() as snapshot_at
from {{ source('telco_stage', 'usage_event') }}
where event_timestamp >= dateadd(day, -30, current_timestamp())
group by service_id, account_id
