select
  account_id,
  service_id,
  count(*) as interaction_count_30d,
  max(interaction_timestamp) as last_interaction_at,
  current_timestamp() as snapshot_at
from {{ source('telco_stage', 'customer_interaction') }}
where interaction_timestamp >= dateadd(day, -30, current_timestamp())
group by account_id, service_id
