select
  hk_account,
  account_id,
  party_id,
  account_number,
  account_type,
  account_status,
  account_created_at,
  account_closed_at,
  hd_account_profile as hashdiff,
  load_dts,
  record_source
from {{ ref('stg_telco__account') }}
