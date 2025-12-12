# list_files.py
import os, json, boto3, logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get('AWS_REGION','us-east-1')
FILES_TABLE = os.environ.get('FILES_TABLE','GBCFinalProjects-Files')
dynamodb = boto3.resource('dynamodb', region_name=REGION)

def lambda_handler(event, context):
    logger.info("Event: %s", event)
    user_sub = event.get('requestContext',{}).get('authorizer',{}).get('claims',{}).get('sub')
    if not user_sub:
        return {"statusCode":401,"body":json.dumps({"message":"unauthorized"})}

    # query by userId GSI or scan filter if no GSI
    table = dynamodb.Table(FILES_TABLE)
    # if you created a GSI on userId, use query. Fallback to scan:
    resp = table.query(IndexName='UserIndex', KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_sub)) \
           if 'UserIndex' in [i['IndexName'] for i in table.global_secondary_indexes or []] \
           else table.scan(FilterExpression=boto3.dynamodb.conditions.Attr('userId').eq(user_sub))

    items = resp.get('Items', [])
    return {"statusCode":200,"body":json.dumps({"files": items})}
