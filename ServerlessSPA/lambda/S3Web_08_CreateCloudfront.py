from __future__ import print_function
import json
import boto3
import botocore
import time
import base64
from botocore.exceptions import ClientError

# Description: A Python 3.x Lambda function, launches the S3Web product cloudformation template via Step Function.
# Author: Billy Glenn
# Version: 2019-05-18
# Input parameters: Extracted from Parameter Store
#   
# ==============================================================================
#
# Setup Session(s)
#
# ==============================================================================

session = boto3.Session(region_name='us-east-1')
ssm = session.client('ssm', region_name='us-east-1')
client = boto3.client('cloudformation', region_name='us-east-1')

# ==============================================================================
#
# lambda_handler()
#
# ==============================================================================
def lambda_handler(event, context):
    print("Starting Cloudfront Distribution Creation")

    # Parse input values from event
    pAppName = event['pAppName']

# ==============================================================================
#
# Retrieve Secrets Manager Values
# 
# ============================================================================== 

    # Use this code snippet in your app.
    # If you need more information about configurations or implementing the sample code, visit the AWS docs:   
    # https://aws.amazon.com/developers/getting-started/python/


    # def get_secret():

    secret_name = "/S3Web/" + pAppName + "/Cloudfront-Referer"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    secretclient = boto3.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        
        get_secret_value_response = secretclient.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            referer = get_secret_value_response['SecretString']
        else:
            decoded_referer = base64.b64decode(get_secret_value_response['SecretBinary'])   

   
# ==============================================================================
#
# Retrieve Parameter Store Values
# 
# ==============================================================================
    print("Reading parameters")
    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Environment', WithDecryption=True)
    environment = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/FQDN', WithDecryption=True)
    fqdn = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Owner', WithDecryption=True)
    owner = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/AppName', WithDecryption=True)
    appname = parameter['Parameter']['Value']

    # parameter = ssm.get_parameter(Name='/general/appid', WithDecryption=True)
    # appid = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/CertARN', WithDecryption=True)
    certarn = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/WafGlobalWebAcl', WithDecryption=True)
    wafglobalwebacl = parameter['Parameter']['Value']

    StackNameValue = appname + "-cloudfront"
    print("Launching CloudFormation Stack " + StackNameValue)

    response = client.create_stack(
    StackName = StackNameValue,
    TemplateURL = 'https://s3-us-west-2.amazonaws.com/ccoe-template-repo/s3web/05_aws-cfn-cloudfront.yaml',
    Parameters = [
        {
            'ParameterKey': 'pEnv',
            'ParameterValue': environment
        },
        {
            'ParameterKey': 'pSiteName',
            'ParameterValue': fqdn
        },
        {
            'ParameterKey': 'pCFNOwnerTag',
            'ParameterValue': owner
        },
        {
            'ParameterKey': 'pApplicationName',
            'ParameterValue': appname
        },
        {
            'ParameterKey': 'pCFCertificateArn',
            'ParameterValue': certarn
        },
        # {
        #     'ParameterKey': 'pAppID',
        #     'ParameterValue': appid
        # },                
        {
            'ParameterKey': 'pRefererValue',
            'ParameterValue': referer
        },
        {
            'ParameterKey': 'pWebACLId',
            'ParameterValue': wafglobalwebacl
        }
    ],
    TimeoutInMinutes=60,
    Capabilities=[
        'CAPABILITY_NAMED_IAM'
    ],
    RoleARN='arn:aws:iam::514712703977:role/S3WebCloudFormationExecutionRole',
    OnFailure='DELETE',
    Tags=[
        {
            'Key': 'Owner',
            'Value': 'bdg3'
        },
      ]
    )

    try:
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/CloudfrontStack', Value=StackNameValue, Type='String', Overwrite=True)
    except botocore.exceptions.ClientError as e:
        print(e)
        payload = {
            "status":False,
            "payload": {
                "AppName": pAppName,
                "payload": "put_parameter() failed."
            }
        }
        return payload