with source as (
    select * from {{ source('telco_stage', 'party') }}
),

renamed as (
    select
        party_id,
        party_type,
        status,
        created_at,
        updated_at
    from source
)

select * from renamed

