# TradeJoy Headless Backend

This is a headless backend-only version of the OpenHands project, optimized for running without a UI.

## Local Development

To run the headless backend locally:

```bash
# Build the Docker image
cd tradejoy
docker-compose build

# Run the container
docker-compose up -d
```

The backend API will be available at `http://localhost:3000`.

## AWS Deployment

This repository includes an automated GitHub Actions workflow for deploying to AWS EC2.

### Required GitHub Secrets

Set up the following secrets in your GitHub repository:

- `AWS_ACCESS_KEY_ID`: AWS access key with ECR and EC2 permissions
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (e.g., us-east-1)
- `EC2_HOST`: Public IP or hostname of your EC2 instance
- `EC2_USER`: SSH username (typically 'ec2-user' or 'ubuntu')
- `EC2_SSH_KEY`: Private SSH key for connecting to the EC2 instance
- `BEDROCK_MODEL`: Amazon Bedrock model identifier (default: bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0)

### EC2 Instance Setup

1. Create an EC2 instance with Docker installed
2. Configure security groups to allow inbound traffic on port 3000
3. Ensure the instance has an IAM role with ECR pull permissions

### Manual Deployment

If you need to deploy manually without GitHub Actions:

```bash
# Build the image
docker build -t tradejoy-backend:latest -f tradejoy/containers/Dockerfile .

# Run the container
docker run -d \
  --name tradejoy-backend \
  --restart unless-stopped \
  -p 3000:3000 \
  -e AWS_ACCESS_KEY_ID=your_key_id \
  -e AWS_SECRET_ACCESS_KEY=your_secret_key \
  -e AWS_REGION=your_region \
  -e BEDROCK_MODEL=bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0 \
  -v /path/to/workspace:/app/workspace \
  tradejoy-backend:latest
```

## Troubleshooting AWS Credentials

If you encounter AWS authentication errors like:

```
litellm.AuthenticationError: BedrockException Invalid Authentication - Unable to locate credentials
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

Follow these steps:

1. **Verify AWS Credentials**: Ensure you've properly set AWS credentials in your environment:

   ```bash
   # For local testing
   export AWS_ACCESS_KEY_ID=your_key_id
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   
   # Then run docker-compose
   docker-compose up -d
   ```

2. **Test AWS Configuration**: The container includes a test script to validate your AWS setup:

   ```bash
   # Shell into the container
   docker exec -it tradejoy-backend bash
   
   # Run the test script
   python /app/tradejoy/containers/test_aws.py
   ```

3. **Check Bedrock Access**: Ensure your AWS account has access to Amazon Bedrock:
   - Bedrock requires explicit enablement in the AWS console
   - Your IAM user needs `bedrock:InvokeModel` permissions
   - Verify the Bedrock model ID is correct and available in your region

4. **Check config.toml**: Verify your configuration has the correct AWS settings:

   ```toml
   [llm]
   model = "bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0"
   aws_region_name = "us-east-1"
   aws_access_key = "YOUR_ACCESS_KEY"
   aws_secret_key = "YOUR_SECRET_KEY"
   base_url = "https://bedrock-runtime.us-east-1.amazonaws.com"
   ```

5. **AWS Region**: Ensure you're using a region where Bedrock is available (e.g., `us-east-1`, `us-west-2`)

6. **Restart Container**: After making changes, restart the container:

   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Common Issues

1. **Missing AWS Credentials**: Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are properly set
2. **Permissions**: Your AWS IAM user must have permissions for Bedrock services
3. **Region**: Bedrock is not available in all AWS regions
4. **Bedrock Access**: Your AWS account might need explicit enablement for Bedrock 