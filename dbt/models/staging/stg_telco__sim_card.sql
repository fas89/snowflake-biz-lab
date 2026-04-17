with source as (
    select * from {{ source('telco_stage', 'sim_card') }}
),

renamed as (
    select
        sim_id,
        account_id,
        device_id,
        msisdn,
        iccid,
        status,
        activated_at
    from source
)

select * from renamed

