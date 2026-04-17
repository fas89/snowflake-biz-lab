with source as (
    select * from {{ source('telco_stage', 'product_offering') }}
),

renamed as (
    select
        product_offering_id,
        name,
        category,
        data_limit_gb,
        voice_limit_min,
        price_chf,
        status,
        created_at
    from source
)

select * from renamed

