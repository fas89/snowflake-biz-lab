with source as (
    select * from {{ source('telco_stage', 'device') }}
),

renamed as (
    select
        device_id,
        account_id,
        device_type,
        manufacturer,
        model,
        imei,
        status,
        registered_at
    from source
)

select * from renamed

