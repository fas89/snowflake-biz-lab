select distinct
  hk_link_service_subscription,
  hk_service,
  hk_subscription,
  load_dts,
  record_source
from (
  select
    s.hk_link_service_subscription,
    sv.hk_service,
    s.hk_subscription,
    greatest(sv.load_dts, s.load_dts) as load_dts,
    'TELCO_DV2.LINK_SERVICE_SUBSCRIPTION' as record_source
  from {{ ref('stg_telco__subscription') }} s
  join {{ ref('stg_telco__service') }} sv
    on s.service_id = sv.service_id
)
