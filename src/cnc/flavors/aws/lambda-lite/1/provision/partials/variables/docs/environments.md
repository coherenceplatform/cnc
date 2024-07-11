###########################
# Environments
###########################

#### `name`

- **Description**: Name to be used as an identifier for all resources.
- **Type**: `string`
- **Default**: `{{ env_collection.name | default('cnc') }}`
  - This default value is derived from an environment variable `env_collection.name` if available, otherwise defaults to `'cnc'`.

#### `environment`

- **Description**: Environment to be used as an identifier for all resources.
- **Type**: `string`
- **Default**: `dev`
  - This default value is set to `'dev'` unless overridden by an environment variable.

#### `account_id`

- **Description**: AWS account ID to be used as an identifier for all resources.
- **Type**: `string`
- **Default**: `{{ env_collection.account_id | default('null') }}`
  - This default value is derived from an environment variable `env_collection.account_id` if available, otherwise defaults to `'null'`.

#### `region`

- **Description**: AWS region to be used for resource deployment.
- **Type**: `string`
- **Default**: `{{ env_collection.region | default('us-east-1') }}`
  - This default value is derived from an environment variable `env_collection.region` if available, otherwise defaults to `'us-east-1'`.
