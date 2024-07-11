###########################
# Lambda
###########################

#### `aws_resources_permission_lambda`

- **Description**: List of AWS resources that the Lambda function needs to access.
- **Type**: `list(string)`
- **Default**: `[ "logs", "cloudwatch", "ec2", "dynamodb", "s3" ]`
  - Specifies the AWS services (as strings) that the Lambda function will have permissions to access.

#### `handler`

- **Description**: Lambda function handler in the format `filename.lambda_handler`.
- **Type**: `string`
- **Default**: `dynamodb.lambda_handler`
  - Specifies the entry point for the Lambda function within the package.

#### `runtime`

- **Description**: Lambda function runtime environment.
- **Type**: `string`
- **Default**: `python3.12`
  - Specifies the Python version used for executing the Lambda function.

#### `lambda_variables`

- **Description**: Environment variables to pass to the Lambda function.
- **Type**: `map(string)`
- **Default**: `{ "REGION_NAME" = "us-east-2" }`
  - Specifies key-value pairs of environment variables for the Lambda function.

#### `type_package_lambda_function`

- **Description**: Method to package the Lambda function.
- **Type**: `string`
- **Default**: `filename`
  - Specifies the method used to package the Lambda function (options: `s3`, `filename`, `image`).

#### `s3_object_key`

- **Description**: S3 key to store the Lambda function package.
- **Type**: `string`
- **Default**: `dynamodb.zip`
  - Specifies the object key under which the Lambda function package will be stored in S3.

#### `s3_bucket_notification_filter_suffix`

- **Description**: Suffix to filter S3 bucket notifications.
- **Type**: `string`
- **Default**: `.zip`
  - Specifies the suffix used to filter notifications for objects stored in the S3 bucket.

#### `logging_log_format`

- **Description**: Log format for the CloudWatch log group.
- **Type**: `string`
- **Default**: `Text`
  - Specifies the format of logs stored in the associated CloudWatch log group.

#### `source_dir`

- **Description**: Directory path containing the Lambda function package.
- **Type**: `string`
- **Default**: `/home/cnc-lambda-function/input/`
  - Specifies the local directory path where the Lambda function package files are located.

#### `output_path`

- **Description**: Output path for the Lambda function package.
- **Type**: `string`
- **Default**: `/home/cnc-lambda-function/output/dynamodb.zip`
  - Specifies the local path where the Lambda function package will be generated or stored after packaging.

#### `image_uri`

- **Description**: URI of the Lambda function image.
- **Type**: `string`
- **Default**: `""`
  - Specifies the URI of the Docker image if the Lambda function is deployed as a container image.

