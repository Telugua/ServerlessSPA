from __future__ import print_function
import json
import boto3
import botocore
import time

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

    # Parse input values from event
    # print(event)
    pAppName = event['pAppName']
    # print("Retrieved AppName value is: " + pAppName)

# ==============================================================================
#
# Retrieve Parameter Store Values
# 
# ==============================================================================

    ps_val1 = '/S3Web/' + pAppName + '/FQDN'
    print("ps_val1 = " + ps_val1)
    parameter = ssm.get_parameter(Name=ps_val1, WithDecryption=True)
    fqdn = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Route53AssumedRoleARN', WithDecryption=True)
    route53assumedrolearn = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Route53PublicHostedZone', WithDecryption=True)
    route53publichostedzone = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Owner', WithDecryption=True)
    owner = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/AppName', WithDecryption=True)
    appname = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Environment', WithDecryption=True)
    environment = parameter['Parameter']['Value']

    StackNameValue = appname + "-cert"
    print(StackNameValue)

    response = client.create_stack(
    StackName = StackNameValue,
    TemplateURL = 'https://s3-us-west-2.amazonaws.com/ccoe-template-repo/s3web/02_aws-cfn-certificate-shared-stepfunction.yml',
    Parameters = [
        {
            'ParameterKey': 'pCertificateSubject',
            'ParameterValue': fqdn
        },
        {
            'ParameterKey': 'pHostedZoneId',
            'ParameterValue': route53publichostedzone
        },
        {
            'ParameterKey': 'pRoute53AssumedRoleArn',
            'ParameterValue': route53assumedrolearn
        },        
        {
            'ParameterKey': 'pCFNOwnerTag',
            'ParameterValue': owner
        },
        {
            'ParameterKey': 'pAppName',
            'ParameterValue': appname
        },
        {
            'ParameterKey': 'pEnv',
            'ParameterValue': environment
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

    try:
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/CertStack', Value=StackNameValue, Type='String', Overwrite=True)
    except botocore.exceptions.ClientError as e:
        print(e)
        payload = {
            "status":False,
            "payload": {
                "AppName": appname,
                "payload": "put_parameter() failed."
            }
        }
        return payload