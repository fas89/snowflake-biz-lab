select distinct
  hk_product_offering,
  product_offering_id,
  load_dts,
  record_source
from {{ ref('stg_telco__product_offering') }}
