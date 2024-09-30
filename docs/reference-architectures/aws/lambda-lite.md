---
title: Lambda Lite Deep Dive
description: What does CNC deploy to my AWS cloud account with the Lambda Lite reference architecture?
---

## Introduction

`lambda-lite` is a free-friendly AWS reference architecture that will use serverless deployments to provide a low-cost footprint. Some services do cost money per-month and with enough scale and usage Lambda and Dynamo will have some cost, but this is a hobby-friendly deployment that is easy to use and versatile.

## Resources Used

### Networking

- A unique [VPC](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) is configured for each application. Multiple services in one application share a VPC.
    - The VPC includes both public and private subnets. Lambda functions are configured to run within this VPC for enhanced security and connectivity to other resources.
- [Lambda Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html) are used to provide HTTP(S) endpoints for your Lambda functions, removing the need for an API Gateway.

### Serverless Compute

- [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) is used as the primary compute service for running your application code.
    - Lambda functions are deployed with configurable runtime and handler settings.
    - VPC configuration is applied to Lambda functions for network isolation and security.
    - Lambda Function URLs are created to provide direct HTTP access to your functions.

### Data Storage

- [DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html) is used as the primary database service.
    - Tables are created with configurable settings such as billing mode, read/write capacity, and global secondary indexes.
    - Point-in-time recovery and TTL can be enabled on tables as needed.

### Build & Deploy

- The build process involves creating a ZIP file of your Lambda function code.
- Deployment updates the Lambda function code and configuration, including environment variables.

### Observability & Monitoring

- [CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html) Logs are configured for Lambda functions to enable logging and monitoring.

### Security & Configuration

- [IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) Roles and Policies are created to provide necessary permissions to Lambda functions.
    - Roles are created with permissions to access DynamoDB, CloudWatch logs, and other specified AWS services.
- [Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html) can be used to store sensitive environment variables.
- VPC Endpoints are created for DynamoDB to allow secure access from within the VPC without traversing the public internet.

### Default Tags

For convenience and auditability, CNC adds default tags to all cloud resources where applicable:
```terraform
    tags = {
        Name = "<resource-specific-name>"
        Environment = "your-collection-name"
        ManagedBy = "cnc"
        Application = "your-application-name"
    }
```

## Key Features

1. **Serverless Architecture**: Utilizes AWS Lambda for a truly serverless application, enabling automatic scaling and pay-per-use pricing.
2. **Simplified API Access**: Lambda Function URLs provide direct HTTP(S) access to your functions without the need for API Gateway.
3. **DynamoDB Integration**: Offers a serverless database solution that scales automatically with your application needs.
4. **VPC Integration**: Lambda functions run within a VPC for enhanced security and connectivity to other AWS resources.
5. **Customizable Configurations**: Allows for easy customization of Lambda function settings, DynamoDB table configurations, and more through `cnc.yml` and `environments.yml` files.

## Considerations

- **Cold Starts**: Be aware of potential cold start times for Lambda functions, especially when running within a VPC.
- **DynamoDB Costs**: While DynamoDB offers a generous free tier, be mindful of read/write capacity settings and consider using on-demand pricing for unpredictable workloads.
- **Function Limits**: Be aware of AWS Lambda limits such as execution time, memory, and concurrent executions.

## Getting Started

Here's an example app that you can put at `index.py` in alongside the following `cnc.yml` and `environments.yml` to get started:

```python
import json
import boto3
import os
from botocore.exceptions import ClientError

# Initialize DynamoDB client and resource
dynamodb_client = boto3.client("dynamodb")
dynamodb_resource = boto3.resource("dynamodb")
table_name = os.environ['DYNAMODB_TABLE']
table = dynamodb_resource.Table(table_name)


def ensure_attribute_exists(attribute_name, attribute_type):
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        existing_attributes = [
            attr["AttributeName"] for attr in response["Table"]["AttributeDefinitions"]
        ]

        if attribute_name not in existing_attributes:
            dynamodb_client.update_table(
                TableName=table_name,
                AttributeDefinitions=[
                    {"AttributeName": attribute_name, "AttributeType": attribute_type},
                ],
                GlobalSecondaryIndexUpdates=[
                    {
                        "Create": {
                            "IndexName": f"{attribute_name}-index",
                            "KeySchema": [
                                {"AttributeName": attribute_name, "KeyType": "HASH"},
                            ],
                            "Projection": {"ProjectionType": "ALL"},
                            "ProvisionedThroughput": {
                                "ReadCapacityUnits": 5,
                                "WriteCapacityUnits": 5,
                            },
                        }
                    },
                ],
            )
            print(f"Added attribute {attribute_name} to the table schema")
    except ClientError as e:
        print(f"Error updating table schema: {str(e)}")


def handler(event, context):
    # Ensure 'message' and 'timestamp' attributes exist
    ensure_attribute_exists("message", "S")
    ensure_attribute_exists("timestamp", "N")

    # Generate a unique ID for our item
    unique_id = context.aws_request_id

    # Item to be written to DynamoDB
    item = {
        "UserID": unique_id,
        "message": f"Hello from Lambda! Your request ID is {unique_id}",
        "timestamp": str(context.get_remaining_time_in_millis()),
        "var_type": os.environ.get("type"),
    }

    try:
        # Write the item to DynamoDB
        table.put_item(Item=item)

        # Retrieve the item from DynamoDB
        response = table.get_item(Key={"UserID": unique_id})

        if "Item" in response:
            retrieved_item = response["Item"]
            return {
                "statusCode": 200,
                "body": json.dumps(retrieved_item),
                "headers": {"Content-Type": "application/json"},
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps("Item not found"),
                "headers": {"Content-Type": "application/json"},
            }
    except ClientError as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error interacting with DynamoDB: {str(e)}"),
            "headers": {"Content-Type": "application/json"},
        }
```

To use this flavor, specify `lambda-lite` as your flavor in the `environments.yml` file:

```yaml
name: my-serverless-app
provider: aws
flavor: lambda-lite
version: 1

collections:
- name: dev
  region: us-east-1
  account_id: "123456789012"
  environments:
  - name: staging
    environment_variables:
    - name: ENVIRONMENT
      value: staging
```

In your `cnc.yml`, define your Lambda function and DynamoDB table:

```yaml
services:
  app:
    x-cnc:
      type: serverless
      handler: "index.handler"
      runtime: "python3.11"
    build:
      context: .

  users-table:
    x-cnc:
      type: dynamodb
      billing_mode: "PAY_PER_REQUEST" # optional, can also be "PROVISIONED", default is PAY_PER_REQUEST
      hash_key: "UserId" # optional, any key
      read_capacity: 5 # optional, default 5
      write_capacity: 5 # optional, default 5
      table_class: "STANDARD" # optional, default "STANDARD", can be "STANDARD_INFREQUENT_ACCESS"
      deletion_protection_enabled: "true" # optional, default is "false"

```

With this configuration, CNC will set up a Lambda function with a Function URL for HTTP access, a DynamoDB table, and the necessary networking and security configurations to connect them securely.