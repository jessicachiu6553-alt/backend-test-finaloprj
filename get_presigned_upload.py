import os, json, boto3, logging
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get('AWS_REGION','us-east-1')
USERS_TABLE = os.environ.get('USER_TABLE','GBCFinalProjects-Users')
FILES_TABLE = os.environ.get('FILES_TABLE','GBCFinalProjects-Files')

logger.info(f"REGION = {REGION}")
logger.info(f"USERS_TABLE = {USERS_TABLE}")
logger.info(f"FILES_TABLE = {FILES_TABLE}")

dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body') or '{}')
        filename = body.get('filename')
        content_type = body.get('contentType','application/octet-stream')
        claims = event['requestContext']['authorizer']['claims']
        user_sub = claims['sub']

        user = dynamodb.Table(USERS_TABLE).get_item(Key={'userId': user_sub}).get('Item')
        if not user:
            return {'statusCode':404, 'body': json.dumps({'message':'user not found'})}
        bucket = user['bucketName']

        key = f"{user_sub}/{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{filename}"

        # Try to generate presigned URL
        try:
            url = s3.generate_presigned_url(
                'put_object', 
                Params={
                    'Bucket': bucket, 
                    'Key': key, 
                    'ContentType': content_type
                }, 
                ExpiresIn=3600
            )
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT"
                },
                'body': json.dumps({'message': 'Failed to generate upload URL'})
            }

        # Only write to DynamoDB if URL generation succeeded
        dynamodb.Table(FILES_TABLE).put_item(Item={
            'fieldId': key,
            'fileId': key,
            'userId': user_sub,
            'fileName': filename,
            's3Key': key,
            'contentType': content_type,
            'createdAt': int(datetime.utcnow().timestamp())
        })

        return {
            'statusCode':200,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT"
            },
            'body': json.dumps({'uploadUrl': url, 's3Key': key})
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT"
            },
            'body': json.dumps({'message': 'Internal server error'})
        }







