with source as (
    select * from {{ source('telco_stage', 'account') }}
),

renamed as (
    select
        account_id,
        party_id,
        account_number,
        account_type,
        status,
        created_at,
        closed_at
    from source
)

select * from renamed

