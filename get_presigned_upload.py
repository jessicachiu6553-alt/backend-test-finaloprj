# import json

# def lambda_handler(event, context):
#     # TODO implement
#     return {
#         'statusCode': 200,
#         'body': json.dumps('Hello from Lambda!')
#     }

# get_presigned_upload.py
import os, json, boto3, logging
from datetime import datetime

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
    url = s3.generate_presigned_url(
        'put_object', 
        Params={
            'Bucket': bucket, 
            'Key': key, 
            'ContentType': content_type
            }, 
        ExpiresIn=3600
    )

    # write metadata
    dynamodb.Table(FILES_TABLE).put_item(Item={
        'fieldId':key,
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





