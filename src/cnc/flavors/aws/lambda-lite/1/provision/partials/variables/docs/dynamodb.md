###########################
# DynamoDB Table
###########################

#### `billing_mode`

- **Description**: The billing mode for the DynamoDB table.
- **Type**: `string`
- **Default**: `PAY_PER_REQUEST`

#### `hash_key`

- **Description**: The hash key for the DynamoDB table.
- **Type**: `string`
- **Default**: `UserID`

#### `read_capacity`

- **Description**: The read capacity for the DynamoDB table.
- **Type**: `number`
- **Default**: `5`

#### `write_capacity`

- **Description**: The write capacity for the DynamoDB table.
- **Type**: `number`
- **Default**: `5`

#### `attributes`

- **Description**: The attributes for the DynamoDB table.
- **Type**: `list(object({ name = string, type = string }))`
- **Default**: `[ { name = "UserID", type = "S" } ]`

#### `global_secondary_indexes`

- **Description**: The global secondary indexes for the DynamoDB table.
- **Type**: `list(object({ name = string, hash_key = string, range_key = string, read_capacity = number, write_capacity = number, projection_type = string }))`
- **Default**: Empty list (`[]`)

#### `deletion_protection_enabled`

- **Description**: Whether to enable deletion protection for the DynamoDB table.
- **Type**: `bool`
- **Default**: `false`

#### `table_class`

- **Description**: The class of the DynamoDB table.
- **Type**: `string`
- **Default**: `STANDARD`

#### `point_in_time_recovery_enabled`

- **Description**: Whether to enable point-in-time recovery for the DynamoDB table.
- **Type**: `bool`
- **Default**: `false`

#### `ttl_enabled`

- **Description**: Whether to enable TTL (Time to Live) for the DynamoDB table.
- **Type**: `bool`
- **Default**: `false`

#### `ttl_attribute_name`

- **Description**: The name of the TTL attribute for the DynamoDB table.
- **Type**: `string`
- **Default**: Empty (`""`)
