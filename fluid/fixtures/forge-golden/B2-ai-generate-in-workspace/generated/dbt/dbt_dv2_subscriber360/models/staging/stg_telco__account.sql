select
  account_id,
  party_id,
  account_number,
  account_type,
  status as account_status,
  created_at as account_created_at,
  closed_at as account_closed_at,
  {{ dv2_hash(["account_id"]) }} as hk_account,
  {{ dv2_hashdiff(["party_id", "account_number", "account_type", "status", "created_at", "closed_at"]) }} as hd_account_profile,
  current_timestamp() as load_dts,
  'TELCO_STAGE.ACCOUNT' as record_source
from {{ source('telco_stage', 'account') }}
