from __future__ import print_function
import json
import boto3
import botocore
import time
from botocore.exceptions import ClientError

# Description: A Python 3.x Lambda function, launches the S3Web product cloudformation template via Step Function.
# Author: Avinash Chowdary Vikram
# Input parameters: Extracted from Parameter Store
#   
# ==============================================================================
#
# Setup Session(s)
#
# ==============================================================================

session = boto3.Session(region_name='us-east-1')
ssm = session.client('ssm', region_name='us-east-1')
cfclient = boto3.client('cloudformation', region_name='us-east-1')

# ==============================================================================
#
# lambda_handler()
#
# ==============================================================================
def lambda_handler(event, context):

    # Parse input values from event
    pAppName = event['pAppName']

# ==============================================================================
#
# Retrieve Parameter Store Values
# 
# ==============================================================================
    print("Reading Parameters")
    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/FQDN', WithDecryption=True)
    fqdn = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Owner', WithDecryption=True)
    owner = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/AppName', WithDecryption=True)
    appname = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/BuildSpec', WithDecryption=True)
    buildspec = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/AppId', WithDecryption=True)
    appid = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Environment', WithDecryption=True)
    environment = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/GithubAccount', WithDecryption=True)
    githubaccount = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/GithubRepo', WithDecryption=True)
    githubrepo = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/GithubRepoBranch', WithDecryption=True)
    githubrepobranch = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/general/notify', WithDecryption=True)
    notify = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/general/order', WithDecryption=True)
    ordernumber = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/general/project', WithDecryption=True)
    project = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/general/org', WithDecryption=True)
    org = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/general/owner', WithDecryption=True)
    owner = parameter['Parameter']['Value']
# ==============================================================================
#
# Retrieve Secrets Manager Values
# 
# ============================================================================== 

    secret_referer = "/S3Web/" + pAppName + "/Cloudfront-Referer"
    secret_githubtoken = "/S3Web/" + pAppName + "/GithubOauthToken"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    smclient = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        referer_response = smclient.get_secret_value(
            SecretId=secret_referer
        )
        githubtoken_response = smclient.get_secret_value(
            SecretId=secret_githubtoken
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
        if 'SecretString' in referer_response:
            referer = referer_response['SecretString']
        else:
            decoded_referer = base64.b64decode(referer_response['SecretBinary'])

        if 'SecretString' in githubtoken_response:
            githubtoken = githubtoken_response['SecretString']
        else:
            decoded_githubtoken = base64.b64decode(githubtoken_response['SecretBinary'])
        
            
    # print("Referer string = " + referer)
    # print("GitHubToken string = " + githubtoken)

    # ==============================================================================
    #
    # Launch CloudFormation Template
    # 
    # ==============================================================================

    StackNameValue = appname + "-S3Web"
    print(StackNameValue)
    print("Launching S3Web and Pipeline stack: " + StackNameValue)
    
    response = cfclient.create_stack(
    StackName = StackNameValue,
    TemplateURL = 'https://s3-us-west-2.amazonaws.com/ccoe-template-repo/s3web/03_aws-cfn-s3web-pipeline-buildspec-stepfunction.yaml',
    Parameters = [
        {
            'ParameterKey': 'pWebsiteFQDN',
            'ParameterValue': fqdn
        },
        {
            'ParameterKey': 'pApplicationName',
            'ParameterValue': appname
        },
        {
            'ParameterKey': 'pBuildSpec',
            'ParameterValue': buildspec
        },        
        {
            'ParameterKey': 'pAppID',
            'ParameterValue': appid
        },                
        {
            'ParameterKey': 'pCFNOwnerTag',
            'ParameterValue': owner
        },
        {
            'ParameterKey': 'pReferer',
            'ParameterValue': referer
        },
        {
            'ParameterKey': 'pGitHubAccount',
            'ParameterValue': githubaccount
        },
        {
            'ParameterKey': 'pGitHubRepo',
            'ParameterValue': githubrepo
        },
        {
            'ParameterKey': 'pGitHubRepoBranch',
            'ParameterValue': githubrepobranch
        },
        {
            'ParameterKey': 'pGitHubToken',
            'ParameterValue': githubtoken
        },                
        {
            'ParameterKey': 'pEnv',
            'ParameterValue': environment
        },
        {
            'ParameterKey': 'pOrderNumber',
            'ParameterValue': ordernumber
        },
        {
            'ParameterKey': 'pNotify',
            'ParameterValue': notify
        },
        {
            'ParameterKey': 'pProjectName',
            'ParameterValue': project
        },
        {
            'ParameterKey': 'pOrg',
            'ParameterValue': org
        }                                
    ],
    TimeoutInMinutes=30,
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
    print("Invocation complete")
    
    try:
        print("Writing stackname to parameter store /S3Web/" + appname + "/S3WebStack")
        ssm.put_parameter(Name='/S3Web/' + appname + '/S3WebStack', Value=StackNameValue, Type='String', Overwrite=True)
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