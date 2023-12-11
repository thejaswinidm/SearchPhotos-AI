import json
import boto3
import base64
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch import Elasticsearch
import time
from requests_aws4auth import AWS4Auth
import requests


def lambda_handler(event, context):
    print(event)
    s3info=event['Records'][0]['s3']
    bucketname=event['Records'][0]['s3']['bucket']['name']
    image=event['Records'][0]['s3']['object']['key']
    #print(bucketname)
    #print(image)
    s3obj = boto3.client('s3')
    getobj=s3obj.get_object(Bucket=bucketname,Key=image)
    body=getobj['Body'].read()
    imagebase64 = body
    
    headobj=s3obj.head_object(Bucket=bucketname,Key=image)
    
    print("headers",headobj['ResponseMetadata']['HTTPHeaders'])
    
    rkclient = boto3.client('rekognition', region_name='us-west-2')
    #response = rkclient.detect_labels(Image={'S3Object':{'Bucket':bucketname,'Name':image}}, MaxLabels=10,MinConfidence = 85)
    # 'Bytes':image
    response = rkclient.detect_labels(Image={'Bytes':imagebase64}, MaxLabels=10,MinConfidence = 85)
    labels=response['Labels']
    customlabels=[]
    for i in labels:
        customlabels.append(i['Name'])
    timestammp = time.gmtime()
    timecreated = time.strftime("%Y-%m-%dT%H:%M:%S", timestammp)
    customlabels.append(headobj.get('Metadata', {}).get('x-amz-meta-customlabels', '').split(','))
    #customlabels.append(headobj['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'])
    jsonformatfores={
        'objectKey':image,
        'bucket':bucketname,
        'createdTimeStamp':timecreated,
        'labels':customlabels
    }
    print("customlabels", customlabels)
    essearch="https://search-photos-levnwdrxcp3d66qplcguq2wmk4.us-west-2.es.amazonaws.com"
    region = "us-west-2"
    service = "es"
    credentials = boto3.Session().get_credentials()
    print("credentials",credentials.access_key, credentials.secret_key, region, service, credentials.token)

    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    #print("awsauth", awsauth)
    
    essearch=essearch+'/'+'photos'+'/'+'_doc'
    req = requests.post(essearch, auth=awsauth, data=json.dumps(jsonformatfores), headers = { "Content-Type": "application/json" })
 
    print("request", req)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
