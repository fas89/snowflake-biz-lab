# Telco Subscriber 360 DV2 Project

This is the shared Data Vault 2.0 dbt project used by the silver Subscriber 360 demo variants.

The project is intentionally organized around:

- staging models over the seeded telco source tables
- raw vault hubs and links
- business vault satellites for service and support health
- silver marts for Subscriber 360 and Subscriber Health scorecards

The external-reference variant points at this project directly.

The internal-reference variant vendors a copy of this project inside the data product folder.
