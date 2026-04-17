with source as (
    select * from {{ source('telco_stage', 'individual') }}
),

renamed as (
    select
        individual_id,
        party_id,
        first_name,
        last_name,
        email,
        date_of_birth,
        created_at
    from source
)

select * from renamed

