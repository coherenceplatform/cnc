## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.3.0 |
| <a name="requirement_archive"></a> [archive](#requirement\_archive) | >= 2.3.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 4.9.0 |
| <a name="requirement_null"></a> [null](#requirement\_null) | >= 3.0.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_archive"></a> [archive](#provider\_archive) | >= 2.3.0 |
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 4.9.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_iam_policy.lambda_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role.lambda_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.lambda_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_function.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_permission.s3_permission](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_s3_bucket.bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_notification.bucket_notification](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_notification) | resource |
| [aws_s3_object.object](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_object) | resource |
| [archive_file.dir](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [archive_file.file](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [aws_partition.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/partition) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_account_id"></a> [account\_id](#input\_account\_id) | Environment to be used on all the resources as identifier | `string` | `"975635808270"` | no |
| <a name="input_aws_resources_permission_lambda"></a> [aws\_resources\_permission\_lambda](#input\_aws\_resources\_permission\_lambda) | List of AWS resources that the Lambda function needs to access | `list(string)` | <pre>[<br>  "logs",<br>  "cloudwatch"<br>]</pre> | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment to be used on all the resources as identifier | `string` | `"dev"` | no |
| <a name="input_environment_variables"></a> [environment\_variables](#input\_environment\_variables) | Environment variables to pass to the Lambda function | `map(string)` | <pre>{<br>  "REGION_NAME": "us-east-2"<br>}</pre> | no |
| <a name="input_handler"></a> [handler](#input\_handler) | Lambda function handler \| e.g Format: filename.lambda\_handler | `string` | `"dynamodb.lambda_handler"` | no |
| <a name="input_image_uri"></a> [image\_uri](#input\_image\_uri) | URI of the Lambda function image | `string` | `""` | no |
| <a name="input_lambda_function_name"></a> [lambda\_function\_name](#input\_lambda\_function\_name) | Name of the Lambda function | `string` | `""` | no |
| <a name="input_logging_log_format"></a> [logging\_log\_format](#input\_logging\_log\_format) | Log format for the CloudWatch log group | `string` | `"Text"` | no |
| <a name="input_name"></a> [name](#input\_name) | Name to be used on all the resources as identifier | `string` | `"cnc"` | no |
| <a name="input_output_path"></a> [output\_path](#input\_output\_path) | Output of the Lambda function | `string` | `"./lambda-function-output/dynamodb.zip"` | no |
| <a name="input_runtime"></a> [runtime](#input\_runtime) | Lambda function runtime | `string` | `"python3.12"` | no |
| <a name="input_s3_bucket_name"></a> [s3\_bucket\_name](#input\_s3\_bucket\_name) | S3 bucket to store the Lambda function package | `string` | `""` | no |
| <a name="input_s3_bucket_notification_filter_suffix"></a> [s3\_bucket\_notification\_filter\_suffix](#input\_s3\_bucket\_notification\_filter\_suffix) | The suffix to filter the S3 bucket notifications | `string` | `".zip"` | no |
| <a name="input_s3_object_key"></a> [s3\_object\_key](#input\_s3\_object\_key) | S3 key to store the Lambda function package | `string` | `"dynamodb.zip"` | no |
| <a name="input_source_dir"></a> [source\_dir](#input\_source\_dir) | Path Dir to the Lambda function package | `string` | `"./lambda-function/"` | no |
| <a name="input_source_file"></a> [source\_file](#input\_source\_file) | Path to the Lambda function package | `string` | `"./lambda-function/dynamodb.py"` | no |
| <a name="input_type_package_lambda_function"></a> [type\_package\_lambda\_function](#input\_type\_package\_lambda\_function) | Method to package the Lambda function \| Set [ 's3', 'filename', 'image' ] | `string` | `"filename"` | no |
| <a name="input_type_source_lambda_function"></a> [type\_source\_lambda\_function](#input\_type\_source\_lambda\_function) | Source of the Lambda function \| Set [ 'file', 'dir' ] | `string` | `"file"` | no |

## Outputs

No outputs.
