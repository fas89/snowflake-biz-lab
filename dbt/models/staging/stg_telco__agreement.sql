with source as (
    select * from {{ source('telco_stage', 'agreement') }}
),

renamed as (
    select
        agreement_id,
        account_id,
        agreement_type,
        status,
        signed_date,
        effective_date,
        termination_date,
        created_at
    from source
)

select * from renamed

