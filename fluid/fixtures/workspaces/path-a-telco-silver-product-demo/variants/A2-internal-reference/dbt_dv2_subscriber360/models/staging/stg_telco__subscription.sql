select
  subscription_id,
  service_id,
  product_offering_id,
  status as subscription_status,
  start_date,
  end_date,
  renewal_date,
  {{ dv2_hash(["subscription_id"]) }} as hk_subscription,
  {{ dv2_hash(["service_id", "subscription_id"]) }} as hk_link_service_subscription,
  {{ dv2_hashdiff(["product_offering_id", "subscription_status", "start_date", "end_date", "renewal_date"]) }} as hd_subscription_plan,
  current_timestamp() as load_dts,
  'TELCO_STAGE.SUBSCRIPTION' as record_source
from {{ source('telco_stage', 'subscription') }}
