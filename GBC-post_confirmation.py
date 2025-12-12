
import os
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
USER_TABLE = 'GBCFinalProjects-Users'  # e.g., "Users"
logger.info("User table: %s", USER_TABLE)
REGION = os.environ.get('AWS_REGION', 'us-east-1')
BUCKET_PREFIX = os.environ.get('BUCKET_PREFIX', 'store-share-user-')


# ---- NEW: CORS configuration for every user bucket ----
USER_BUCKET_CORS = {
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": [
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "HEAD"
            ],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["Content-Disposition"],
            "MaxAgeSeconds": 3000
        }
    ]
}

def create_bucket(bucket_name):
    try:
        if REGION == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(Bucket=bucket_name,
                             CreateBucketConfiguration={'LocationConstraint': REGION})
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        logger.info(f"Enabled versioning for bucket {bucket_name}")

        # ---- NEW: Apply CORS rules ----
        s3.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=USER_BUCKET_CORS
        )
        logger.info(f"Applied CORS config to bucket {bucket_name}")

    except ClientError as e:
        logger.error("Error creating bucket: %s", e)
        raise

def lambda_handler(event, context):
    # This is invoked by Cognito Post Confirmation
    logger.info("Received event: %s", event)

    user_attrs = event.get('request', {}).get('userAttributes', {})
    sub = user_attrs.get('sub')
    email = user_attrs.get('email')

    if not sub:
        logger.error("No sub found in event")
        return event

    bucket_name = f"{BUCKET_PREFIX}{sub}"

    # Create & configure the S3 bucket
    create_bucket(bucket_name)
    
    logger.info("User table: %s", USER_TABLE)

    # Store user record
    table = dynamodb.Table(USER_TABLE)
    table.put_item(Item={
        'userId': sub,
        'email': email or '',
        'bucketName': bucket_name,
        'isAdmin': False,
        'createdAt': int(context.aws_request_id.split('-')[0], 16)  # simple unique-ish
    })
    logger.info("User record written to DynamoDB for %s", sub)
    return event



