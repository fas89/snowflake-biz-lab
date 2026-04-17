with source as (
    select * from {{ source('telco_stage', 'payment') }}
),

renamed as (
    select
        payment_id,
        invoice_id,
        amount_chf,
        payment_method,
        payment_date,
        status,
        created_at
    from source
)

select * from renamed

