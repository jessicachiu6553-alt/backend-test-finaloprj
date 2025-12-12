# delete_file.py
import os, json, boto3, logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get('AWS_REGION','us-east-1')
USERS_TABLE = os.environ.get('USER_TABLE','GBCFinalProjects-Users')
FILES_TABLE = os.environ.get('FILES_TABLE','GBCFinalProjects-Files')
ROOT_BUCKET = os.environ.get('ROOT_BUCKET','gbc-storage-share-root')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def lambda_handler(event, context):
    logger.info("Event: %s", event)
    body = json.loads(event.get('body') or '{}')
    s3_key = body.get('s3Key')
    if not s3_key:
        return {"statusCode":400,"body":json.dumps({"message":"s3Key required"})}

    user_sub = event.get('requestContext',{}).get('authorizer',{}).get('claims',{}).get('sub')
    if not user_sub:
        return {"statusCode":401,"body":json.dumps({"message":"unauthorized"})}

    rec = dynamodb.Table(FILES_TABLE).get_item(Key={'fileId': s3_key}).get('Item')
    if not rec or rec.get('userId') != user_sub:
        return {"statusCode":403,"body":json.dumps({"message":"not authorized"})}

    user = dynamodb.Table(USERS_TABLE).get_item(Key={'id': user_sub}).get('Item')
    bucket = user.get('bucketName') or ROOT_BUCKET

    # delete S3 object
    s3.delete_object(Bucket=bucket, Key=s3_key)
    # delete metadata
    dynamodb.Table(FILES_TABLE).delete_item(Key={'fileId': s3_key})
    return {"statusCode":200,"body":json.dumps({"message":"deleted"})}


