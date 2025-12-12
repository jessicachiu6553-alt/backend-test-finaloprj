# get_presigned_download.py
import os, json, boto3, logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

USERS_TABLE = os.environ.get('USER_TABLE','Users')
FILES_TABLE = os.environ.get('FILES_TABLE','Files')

def lambda_handler(event, context):
    body = json.loads(event.get('body') or '{}')
    s3_key = body.get('s3Key')
    user_sub = event['requestContext']['authorizer']['claims']['sub']
    item = dynamodb.Table(FILES_TABLE).get_item(Key={'fileId': s3_key}).get('Item')
    if not item or item['userId'] != user_sub:
        return {
            'statusCode':403, 
            'body': json.dumps({'message':'Not authorized'})
            }
    bucket = dynamodb.Table(USERS_TABLE).get_item(Key={'userId': user_sub})['Item']['bucketName']
    
    url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': s3_key}, ExpiresIn=3600)
    
    return {
        'statusCode':200, 
        'body': json.dumps({'downloadUrl': url})
        }


