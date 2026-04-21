{% macro dv2_hash(columns) -%}
md5(
  concat_ws(
    '||',
    {%- for col in columns -%}
    coalesce(cast({{ col }} as varchar), '')
    {%- if not loop.last %}, {% endif -%}
    {%- endfor -%}
  )
)
{%- endmacro %}

{% macro dv2_hashdiff(columns) -%}
{{ dv2_hash(columns) }}
{%- endmacro %}
