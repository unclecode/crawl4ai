# Deploying Crawl4ai on AWS Lambda

This guide walks you through deploying Crawl4ai as an AWS Lambda function with API Gateway integration. You'll learn how to set up, test, and clean up your deployment.

## Prerequisites

Before you begin, ensure you have:

- AWS CLI installed and configured (`aws configure`)
- Docker installed and running
- Python 3.8+ installed
- Basic familiarity with AWS services

## Project Files

Your project directory should contain:

- `Dockerfile`: Container configuration for Lambda
- `lambda_function.py`: Lambda handler code
- `deploy.py`: Our deployment script

## Step 1: Install Required Python Packages

Install the Python packages needed for our deployment script:

```bash
pip install typer rich
```

## Step 2: Run the Deployment Script

Our Python script automates the entire deployment process:

```bash
python deploy.py
```

The script will guide you through:

1. Configuration setup (AWS region, function name, memory allocation)
2. Docker image building
3. ECR repository creation
4. Lambda function deployment
5. API Gateway setup
6. Provisioned concurrency configuration (optional)

Follow the prompts and confirm each step by pressing Enter.

## Step 3: Manual Deployment (Alternative to the Script)

If you prefer to deploy manually or understand what the script does, follow these steps:

### Building and Pushing the Docker Image

```bash
# Build the Docker image
docker build -t crawl4ai-lambda .

# Create an ECR repository (if it doesn't exist)
aws ecr create-repository --repository-name crawl4ai-lambda

# Get ECR login password and login
aws ecr get-login-password | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

# Tag the image
ECR_URI=$(aws ecr describe-repositories --repository-names crawl4ai-lambda --query 'repositories[0].repositoryUri' --output text)
docker tag crawl4ai-lambda:latest $ECR_URI:latest

# Push the image to ECR
docker push $ECR_URI:latest
```

### Creating the Lambda Function

```bash
# Get IAM role ARN (create it if needed)
ROLE_ARN=$(aws iam get-role --role-name lambda-execution-role --query 'Role.Arn' --output text)

# Create Lambda function
aws lambda create-function \
    --function-name crawl4ai-function \
    --package-type Image \
    --code ImageUri=$ECR_URI:latest \
    --role $ROLE_ARN \
    --timeout 300 \
    --memory-size 4096 \
    --ephemeral-storage Size=10240 \
    --environment "Variables={CRAWL4_AI_BASE_DIRECTORY=/tmp/.crawl4ai,HOME=/tmp,PLAYWRIGHT_BROWSERS_PATH=/function/pw-browsers}"
```

If you're updating an existing function:

```bash
# Update function code
aws lambda update-function-code \
    --function-name crawl4ai-function \
    --image-uri $ECR_URI:latest

# Update function configuration
aws lambda update-function-configuration \
    --function-name crawl4ai-function \
    --timeout 300 \
    --memory-size 4096 \
    --ephemeral-storage Size=10240 \
    --environment "Variables={CRAWL4_AI_BASE_DIRECTORY=/tmp/.crawl4ai,HOME=/tmp,PLAYWRIGHT_BROWSERS_PATH=/function/pw-browsers}"
```

### Setting Up API Gateway

```bash
# Create API Gateway
API_ID=$(aws apigateway create-rest-api --name crawl4ai-api --query 'id' --output text)

# Get root resource ID
PARENT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?path==`/`].id' --output text)

# Create resource
RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $PARENT_ID --path-part "crawl" --query 'id' --output text)

# Create POST method
aws apigateway put-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST --authorization-type NONE

# Get Lambda function ARN
LAMBDA_ARN=$(aws lambda get-function --function-name crawl4ai-function --query 'Configuration.FunctionArn' --output text)

# Set Lambda integration
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations

# Deploy API
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod

# Set Lambda permission
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws lambda add-permission \
    --function-name crawl4ai-function \
    --statement-id apigateway \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:$ACCOUNT_ID:$API_ID/*/POST/crawl"
```

### Setting Up Provisioned Concurrency (Optional)

This reduces cold starts:

```bash
# Publish a version
VERSION=$(aws lambda publish-version --function-name crawl4ai-function --query 'Version' --output text)

# Create alias
aws lambda create-alias \
    --function-name crawl4ai-function \
    --name prod \
    --function-version $VERSION

# Configure provisioned concurrency
aws lambda put-provisioned-concurrency-config \
    --function-name crawl4ai-function \
    --qualifier prod \
    --provisioned-concurrent-executions 2

# Update API Gateway to use alias
LAMBDA_ALIAS_ARN="arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:crawl4ai-function:prod"
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ALIAS_ARN/invocations

# Redeploy API Gateway
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod
```

## Step 4: Testing the Deployment

Once deployed, test your function with:

```bash
ENDPOINT_URL="https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/crawl"

# Test with curl
curl -X POST $ENDPOINT_URL \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

Or using Python:

```python
import requests
import json

url = "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/crawl"
payload = {
    "url": "https://example.com",
    "browser_config": {
        "headless": True,
        "verbose": False
    },
    "crawler_config": {
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "markdown_generator": {
                    "type": "DefaultMarkdownGenerator",
                    "params": {
                        "content_filter": {
                            "type": "PruningContentFilter",
                            "params": {
                                "threshold": 0.48,
                                "threshold_type": "fixed"
                            }
                        }
                    }
                }
            }
        }
    }
}

response = requests.post(url, json=payload)
result = response.json()
print(json.dumps(result, indent=2))
```

## Step 5: Cleaning Up Resources

To remove all AWS resources created for this deployment:

```bash
python deploy.py cleanup
```

Or manually:

```bash
# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id $API_ID

# Remove provisioned concurrency (if configured)
aws lambda delete-provisioned-concurrency-config \
    --function-name crawl4ai-function \
    --qualifier prod

# Delete alias (if created)
aws lambda delete-alias \
    --function-name crawl4ai-function \
    --name prod

# Delete Lambda function
aws lambda delete-function --function-name crawl4ai-function

# Delete ECR repository
aws ecr delete-repository --repository-name crawl4ai-lambda --force
```

## Troubleshooting

### Cold Start Issues

If experiencing long cold starts:
- Enable provisioned concurrency
- Increase memory allocation (4096 MB recommended)
- Ensure the Lambda function has enough ephemeral storage

### Permission Errors

If you encounter permission errors:
- Check the IAM role has the necessary permissions
- Ensure API Gateway has permission to invoke the Lambda function

### Container Size Issues

If your container is too large:
- Optimize the Dockerfile
- Use multi-stage builds
- Consider removing unnecessary dependencies

## Performance Considerations

- Lambda memory affects CPU allocation - higher memory means faster execution
- Provisioned concurrency eliminates cold starts but costs more
- Optimize the Playwright setup for faster browser initialization

## Security Best Practices

- Use the principle of least privilege for IAM roles
- Implement API Gateway authentication for production deployments
- Consider using AWS KMS for storing sensitive configuration

## Useful AWS Console Links

Here are quick links to access important AWS console pages for monitoring and managing your deployment:

| Resource | Console Link |
|----------|-------------|
| Lambda Functions | [AWS Lambda Console](https://console.aws.amazon.com/lambda/home#/functions) |
| Lambda Function Logs | [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups) |
| API Gateway | [API Gateway Console](https://console.aws.amazon.com/apigateway/home) |
| ECR Repositories | [ECR Console](https://console.aws.amazon.com/ecr/repositories) |
| IAM Roles | [IAM Console](https://console.aws.amazon.com/iamv2/home#/roles) |
| CloudWatch Metrics | [CloudWatch Metrics](https://console.aws.amazon.com/cloudwatch/home#metricsV2) |

### Monitoring Lambda Execution

To monitor your Lambda function:

1. Go to the [Lambda function console](https://console.aws.amazon.com/lambda/home#/functions)
2. Select your function (`crawl4ai-function`)
3. Click the "Monitor" tab to see:
   - Invocation metrics
   - Success/failure rates
   - Duration statistics

### Viewing Lambda Logs

To see detailed execution logs:

1. Go to [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups)
2. Find the log group named `/aws/lambda/crawl4ai-function`
3. Click to see the latest log streams
4. Each stream contains logs from a function execution

### Checking API Gateway Traffic

To monitor API requests:

1. Go to the [API Gateway console](https://console.aws.amazon.com/apigateway/home)
2. Select your API (`crawl4ai-api`)
3. Click "Dashboard" to see:
   - API calls
   - Latency
   - Error rates

## Conclusion

You now have Crawl4ai running as a serverless function on AWS Lambda! This setup allows you to crawl websites on-demand without maintaining infrastructure, while paying only for the compute time you use.