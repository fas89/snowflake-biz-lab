select distinct
  hk_account,
  account_id,
  load_dts,
  record_source
from {{ ref('stg_telco__account') }}
