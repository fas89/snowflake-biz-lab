with source as (
    select * from {{ source('telco_stage', 'app_event') }}
),

renamed as (
    select
        app_event_id,
        account_id,
        device_id,
        event_type,
        session_minutes,
        event_timestamp
    from source
)

select * from renamed

