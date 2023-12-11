import json
import boto3
import base64
import time
from requests_aws4auth import AWS4Auth
import requests
    
region = 'us-west-2'
esHost="https://search-photos-levnwdrxcp3d66qplcguq2wmk4.us-west-2.es.amazonaws.com"


# Call the function to create the index
def create_photos_index():
    service = "es"
    credentials = boto3.Session().get_credentials()
    aws_auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token
    )
    url = f"{esHost}/photos"  # Specify the index name in the URL

    headers = {"Content-Type": "application/json"}
    mapping = {
        "mappings": {
            "properties": {
                "objectKey": {"type": "keyword"},
                "bucket": {"type": "keyword"},
                "createdTimestamp": {"type": "date"},
                "labels": {"type": "keyword"}
            }
        }
    }

    response = requests.post(url, auth=aws_auth, headers=headers, data=json.dumps(mapping))
    print(response.text)
    response.raise_for_status()
 
def lambda_handler(event, context):
    print('Event:', event)
    query = event['queryStringParameters']["q"] 
    print('query: ',query)
    labels = getLabelsFromLex(query)
    
    result = getDataFromES(labels)
    
    return {
        'statusCode': 200,
        'body': json.dumps(result),
        'headers': {
            "Access-Control-Allow-Headers" : "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        }
        }
    
def getLabelsFromLex(query):
    client = boto3.client('lex-runtime')
    boto3.set_stream_logger('')
    response = client.post_text(
    botName='photosearchbot',
    botAlias="photosearchbot",
    userId="test",
    inputText= query)
    print("response:",response)
    slots = get_slots(response)
    print(slots)
    labels = []
    for slot in slots:
        if slots[slot] is not None:
            # strin = 
            slots[slot] =slots[slot].capitalize()
            labels.append(slots[slot])
            # if 'interpretedValue' in slots[slot]['value']:
            #     labels.append(slots[slot]['value']['interpretedValue'])
            # else:
            #     labels.append(slots[slot]['value']['originalValue'])
    print(labels)
    return labels
	

def get_slots(intent_request):
    return intent_request['slots']
    
def getDataFromES(labels):
    service = "es"
    index = 'photos'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    url = esHost + '/' + index + '/_search'
    
    imageNames = []
    for label in labels:
        print("label: ",label)
        query = {"query": {"match": {"labels": label }}}
        headers = { "Content-Type": "application/json" }
        res = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
        res = res.text
        res = json.loads(res)
        print("resultjson: ",res)
        res = res['hits']['hits']
        for hit in res:
            image = hit['_source']['objectKey']
            if image not in imageNames:
                imageNames.append(image)
        print("result:", res)
    return { 'imagePaths': imageNames}
	