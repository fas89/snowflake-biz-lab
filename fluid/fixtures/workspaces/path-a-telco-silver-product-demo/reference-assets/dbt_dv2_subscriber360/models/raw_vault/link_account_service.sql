select distinct
  hk_link_account_service,
  hk_account,
  hk_service,
  load_dts,
  record_source
from (
  select
    s.hk_link_account_service,
    a.hk_account,
    s.hk_service,
    greatest(a.load_dts, s.load_dts) as load_dts,
    'TELCO_DV2.LINK_ACCOUNT_SERVICE' as record_source
  from {{ ref('stg_telco__service') }} s
  join {{ ref('stg_telco__account') }} a
    on s.account_id = a.account_id
)
