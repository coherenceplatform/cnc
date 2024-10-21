def lambda_handler(event, context):
    return {
        "headers": {"Content-Type": "text/html"},
        "statusCode": 200,
        "body": "Hello from Lambda!",
    }
