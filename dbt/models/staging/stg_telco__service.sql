with source as (
    select * from {{ source('telco_stage', 'service') }}
),

renamed as (
    select
        service_id,
        account_id,
        service_type,
        status,
        activated_at,
        terminated_at
    from source
)

select * from renamed

