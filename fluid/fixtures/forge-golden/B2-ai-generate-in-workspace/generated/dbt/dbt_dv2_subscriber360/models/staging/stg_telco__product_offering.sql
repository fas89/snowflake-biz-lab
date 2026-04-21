select
  product_offering_id,
  name as product_offering_name,
  category as product_category,
  data_limit_gb,
  voice_limit_min,
  price_chf,
  status as product_status,
  {{ dv2_hash(["product_offering_id"]) }} as hk_product_offering,
  {{ dv2_hashdiff(["product_offering_name", "product_category", "data_limit_gb", "voice_limit_min", "price_chf", "product_status"]) }} as hd_product_offering,
  current_timestamp() as load_dts,
  'TELCO_STAGE.PRODUCT_OFFERING' as record_source
from {{ source('telco_stage', 'product_offering') }}
