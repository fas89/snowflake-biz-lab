with source as (
    select * from {{ source('telco_stage', 'subscription') }}
),

renamed as (
    select
        subscription_id,
        service_id,
        product_offering_id,
        status,
        start_date,
        end_date,
        renewal_date,
        created_at
    from source
)

select * from renamed

