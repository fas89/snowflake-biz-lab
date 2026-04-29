-- Deterministic Snowflake DDL snapshot for B1/B2 generated data-model context.
-- Mirrors the seeded TELCO_STAGE_LOAD tables used by the lab.

create table party (
  party_id varchar primary key,
  party_type varchar,
  status varchar,
  created_at timestamp_ntz,
  updated_at timestamp_ntz
);

create table account (
  account_id varchar primary key,
  party_id varchar,
  account_number varchar,
  account_type varchar,
  status varchar,
  created_at timestamp_ntz,
  closed_at timestamp_ntz
);

create table product_offering (
  product_offering_id varchar primary key,
  name varchar,
  category varchar,
  data_limit_gb number(8,2),
  voice_limit_min number,
  price_chf number(10,2),
  status varchar,
  created_at timestamp_ntz
);

create table service (
  service_id varchar primary key,
  account_id varchar,
  service_type varchar,
  status varchar,
  activated_at timestamp_ntz,
  terminated_at timestamp_ntz
);

create table subscription (
  subscription_id varchar primary key,
  service_id varchar,
  product_offering_id varchar,
  status varchar,
  start_date date,
  end_date date,
  renewal_date date,
  created_at timestamp_ntz
);

create table resource (
  resource_id varchar primary key,
  service_id varchar,
  resource_type varchar,
  resource_name varchar,
  resource_status varchar,
  assigned_at timestamp_ntz,
  released_at timestamp_ntz
);

create table usage_event (
  usage_id varchar primary key,
  account_id varchar,
  service_id varchar,
  usage_type varchar,
  quantity number(12,4),
  event_timestamp timestamp_ntz,
  rating_status varchar
);

create table customer_interaction (
  interaction_id varchar primary key,
  account_id varchar,
  service_id varchar,
  channel varchar,
  interaction_type varchar,
  outcome varchar,
  interaction_timestamp timestamp_ntz
);

create table trouble_ticket (
  ticket_id varchar primary key,
  account_id varchar,
  service_id varchar,
  ticket_category varchar,
  severity varchar,
  status varchar,
  opened_at timestamp_ntz,
  resolved_at timestamp_ntz
);

create table invoice (
  invoice_id varchar primary key,
  account_id varchar,
  invoice_number varchar,
  invoice_date date,
  due_date date,
  total_amount_chf number(10,2),
  status varchar,
  created_at timestamp_ntz
);

create table invoice_charge (
  charge_id varchar primary key,
  invoice_id varchar,
  charge_type varchar,
  charge_description varchar,
  quantity number(12,4),
  amount_chf number(10,2),
  charge_date date
);
