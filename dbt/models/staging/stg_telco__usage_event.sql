with source as (
    select * from {{ source('telco_stage', 'usage_event') }}
),

renamed as (
    select
        usage_id,
        account_id,
        service_id,
        usage_type,
        quantity,
        event_timestamp,
        rating_status
    from source
)

select * from renamed

