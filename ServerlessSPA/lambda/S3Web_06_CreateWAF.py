from __future__ import print_function
import json
import boto3
import botocore
import time

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

    # Parse input values from event
    pAppName = event['pAppName']

    StackNameValue = pAppName + "-WAF-PGESource"
    print(StackNameValue)
    print("Invoking CloudFormation template to instantiate WAF Rules.  StackName: " + StackNameValue)

    response = client.create_stack(
    StackName = StackNameValue,
    TemplateURL = 'https://s3-us-west-2.amazonaws.com/ccoe-template-repo/s3web/04_aws-cfn-waf-pge.yaml',
    Parameters = [
        {
            'ParameterKey': 'stackPrefix',
            'ParameterValue': pAppName
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
        print("Writing WAF StackName to parameter store /S3Web/" + pAppName + "/WafStack")
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/WafStack', Value=StackNameValue, Type='String', Overwrite=True)
        print("successfully wrote /s3web/" + pAppName + "/WafStack with value: " + StackNameValue)

    except botocore.exceptions.ClientError as e:
        print(e)
        payload = {
            "status":False,
            "payload": {
                "Parameter": "/S3Web" + pAppName + "/WafStack",
                "payload": "put_parameter() failed."
            }
        }
        return payload
