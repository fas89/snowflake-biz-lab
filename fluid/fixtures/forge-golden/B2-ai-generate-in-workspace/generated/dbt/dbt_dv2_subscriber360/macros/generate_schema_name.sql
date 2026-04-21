-- Route dbt-model `+schema:` configs to the raw custom schema name.
-- dbt's default macro concatenates target.schema + custom → we saw
-- TELCO_FLUID_DEMO_TELCO_FLUID_DEMO when both resolved to the same
-- env var. Returning the custom name verbatim keeps the contract's
-- binding.location.schema (SNOWFLAKE_FLUID_SCHEMA) aligned with where
-- dbt actually materializes the marts.
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
