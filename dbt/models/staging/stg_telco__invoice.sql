with source as (
    select * from {{ source('telco_stage', 'invoice') }}
),

renamed as (
    select
        invoice_id,
        account_id,
        invoice_number,
        invoice_date,
        due_date,
        total_amount_chf,
        status,
        created_at
    from source
)

select * from renamed

