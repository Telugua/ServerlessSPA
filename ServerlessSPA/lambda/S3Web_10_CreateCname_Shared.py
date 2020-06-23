from __future__ import print_function
import json
import boto3
import botocore
import time
import base64
from botocore.exceptions import ClientError

# Description: A Python 3.x Lambda function, launches CloudFormation template via
# via Step Function which creates a Route 53 CNAME record for the Cloudfront
#  Distribution Domain Name associated with the S3 Webapp Pipeline product.
#
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
    print("Starting Route 53 CNAME Creation")

    # Parse input values from event
    pAppName = event['pAppName']

# ==============================================================================
#
# Retrieve Parameter Store Values
# 
# ==============================================================================
    print("Reading parameters")

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/FQDN', WithDecryption=True)
    fqdn = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Route53PrivateHostedZone', WithDecryption=True)
    privatehostedzone = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/DistributionDomainName', WithDecryption=True)
    distributiondomainname = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/AppName', WithDecryption=True)
    appname = parameter['Parameter']['Value']
    

    StackNameValue = appname + "-route53"
    print("Launching CloudFormation Stack " + StackNameValue)

    response = client.create_stack(
    StackName = StackNameValue,
    TemplateURL = 'https://s3-us-west-2.amazonaws.com/ccoe-template-repo/s3web/06_aws-cfn-r53-cname.yaml',
    Parameters = [
        {
            'ParameterKey': 'pWebsiteFQDN',
            'ParameterValue': fqdn
        },
        {
            'ParameterKey': 'pPrivateHostedZoneId',
            'ParameterValue': privatehostedzone
        },
        {
            'ParameterKey': 'pDistributionDomainName',
            'ParameterValue': distributiondomainname
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
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/Route53Stack', Value=StackNameValue, Type='String', Overwrite=True)
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