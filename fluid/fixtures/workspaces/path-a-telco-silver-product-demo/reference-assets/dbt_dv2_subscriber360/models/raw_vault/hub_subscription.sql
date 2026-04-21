select distinct
  hk_subscription,
  subscription_id,
  load_dts,
  record_source
from {{ ref('stg_telco__subscription') }}
