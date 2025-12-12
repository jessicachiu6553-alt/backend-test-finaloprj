# import json

# def lambda_handler(event, context):
#     # TODO implement
#     return {
#         'statusCode': 200,
#         'body': json.dumps('Hello from Lambda!')
#     }



import json
import base64
import urllib.parse
import urllib.request
import os

CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
CLIENT_SECRET = os.environ["COGNITO_CLIENT_SECRET"]
COGNITO_DOMAIN = os.environ["COGNITO_DOMAIN"]  # e.g. https://xxx.auth.us-east-1.amazoncognito.com

def lambda_handler(event, context):
    body = json.loads(event["body"])
    username = body["username"]
    password = body["password"]

    token_url = f"{COGNITO_DOMAIN}/oauth2/token"

    # client_id:client_secret → Base64
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    basic_auth = base64.b64encode(auth_str.encode()).decode()

    data = urllib.parse.urlencode({
        "grant_type": "password",
        "username": username,
        "password": password,
    }).encode()

    req = urllib.request.Request(
        token_url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}"
        }
    )

    try:
        with urllib.request.urlopen(req) as res:
            token_data = json.loads(res.read())
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(token_data)
            }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }




