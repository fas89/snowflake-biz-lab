select
  service_id,
  account_id,
  service_type,
  status as service_status,
  activated_at,
  terminated_at,
  {{ dv2_hash(["service_id"]) }} as hk_service,
  {{ dv2_hash(["account_id", "service_id"]) }} as hk_link_account_service,
  {{ dv2_hashdiff(["account_id", "service_type", "service_status", "activated_at", "terminated_at"]) }} as hd_service_status,
  current_timestamp() as load_dts,
  'TELCO_STAGE.SERVICE' as record_source
from {{ source('telco_stage', 'service') }}
