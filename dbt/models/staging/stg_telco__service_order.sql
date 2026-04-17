with source as (
    select * from {{ source('telco_stage', 'service_order') }}
),

renamed as (
    select
        order_id,
        account_id,
        order_type,
        status,
        order_date,
        fulfillment_date
    from source
)

select * from renamed
