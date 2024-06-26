# DynamoDB Table Configuration Variables

The following configuration describes the available variables for setting up a DynamoDB table using Terraform.

## Variables

- `name`: Name of the application or service. Example: `"cnc"`.
- `environment`: Environment where the table will be provisioned. Example: `"dev"`.

- `table_name`: Name of the DynamoDB table. If not set, defaults to `var.environment + var.name + "dynamodb"`.
- `billing_mode`: Billing mode for the table. Can be `"PAY_PER_REQUEST"` or `"PROVISIONED"`. Default is `"PAY_PER_REQUEST"`.
- `hash_key`: Hash key of the table. Default is `""`.
- `attributes`: List of table attributes, like UserID with type "S".

- `global_secondary_indexes`: Configurable global secondary indexes.

- `read_capacity`: Read capacity of the table. Default is `5`.
- `write_capacity`: Write capacity of the table. Default is `5`.
- `deletion_protection_enabled`: Enables deletion protection. Default is `false`.
- `table_class`: Table class, can be `'STANDARD'` or `'STANDARD_INFREQUENT_ACCESS'`. Default is `'STANDARD'`.
- `point_in_time_recovery_enabled`: Enables point-in-time recovery. Default is `false`.
- `ttl_attribute_name`: TTL (Time to Live) attribute name. Default is `""`.
- `ttl_enabled`: Enables TTL. Default is `false`.

- `dynamodb_tags`: Specific tags for the DynamoDB resource.