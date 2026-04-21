select distinct
  hk_service,
  service_id,
  load_dts,
  record_source
from {{ ref('stg_telco__service') }}
