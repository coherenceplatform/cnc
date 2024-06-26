# Lambda Function Configuration

The following configuration outlines the variables used to set up a Lambda function using Terraform.

## Variables

- `name`: Name of the application or service. Example: `"cnc"`.
- `environment`: Environment where the Lambda function will be deployed. Example: `"dev"`.
- `account_id`: Your AWS account ID.

- `aws_resources_permission_lambda`: Names of AWS resources for Lambda permission, such as logs, CloudWatch, and S3.

- `lambda_function_name`: Name of the Lambda function. If not set, defaults to `var.environment + var.name + "lambda"`.
- `handler`: Handler function for the Lambda. Default is `""`.
- `runtime`: Runtime environment for the Lambda. Default is `"python3.12"`.

- `environment_variables`: Environment variables for the Lambda function. Default is an empty dictionary.

- `s3_bucket_name`: Name of the S3 bucket for deployment artifacts. If not set, defaults to `[local.infrastructure_suffix, "lambda", var.account_id]`.
- `s3_object_key`: Object key for the deployment artifact in S3. Default is `""`.
- `s3_bucket_notification_filter_suffix`: Suffix filter for S3 bucket notifications. Default is `".zip"`.

- `logging_log_format`: Log format for logging. Default is `"Text"`.

- `type_source_lambda_function`: Source type of the Lambda function, either `"file"` or `"dir"`. Default is `"file"`.

- `source_file`: Path to the Lambda function file. Example: `"/home/balmant/Desktop/app-lambda-coherence/dynamodb.py"`.
- `source_dir`: Directory containing the Lambda function source files. Example: `"/home/balmant/Desktop/app-lambda-coherence/"`.
- `output_path`: Path where the Lambda deployment artifact will be generated. Example: `"/home/balmant/Desktop/app-output-lambda/dynamodb.zip"`.

- `image_uri`: URI of the ECR (Elastic Container Registry) image. Example: `"<your-ecr-image>"`.

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