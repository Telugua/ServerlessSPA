# Author:   Ryan Avendano
# Poacher:  Billy Glenn
# Date:     5/2/19
#
# Purpose:          
# Parameters:        
# Pre-Condition:    
# Post-Condition:   

import boto3
import json
from botocore.exceptions import ClientError

# ==============================================================================
#
# Assume Role in Centralized Account
#
#===============================================================================

# Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

# Create IAM client
sts_default_provider_chain = boto3.client('sts')

print('Default Provider Identity: : ' + sts_default_provider_chain.get_caller_identity()['Arn'])

role_to_assume_arn='arn:aws:iam::514712703977:role/S3Web_SES_Role'
role_session_name='S3Web_Notification'

response=sts_default_provider_chain.assume_role(
    RoleArn=role_to_assume_arn,
    RoleSessionName=role_session_name
)

creds=response['Credentials']

sts_assumed_role = boto3.client('sts',
    aws_access_key_id=creds['AccessKeyId'],
    aws_secret_access_key=creds['SecretAccessKey'],
    aws_session_token=creds['SessionToken'],
)

print('AssumedRole Identity: ' + sts_assumed_role.get_caller_identity()['Arn'])

# ==============================================================================
#
# Setup Session(s)
#
# ==============================================================================

session = boto3.Session(region_name='us-east-1')
ssm = session.client('ssm', region_name='us-east-1')


def lambda_handler(event, context):



    parameter = ssm.get_parameter(Name='/s3web/fqdn', WithDecryption=True)
    fqdn = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/general/owner', WithDecryption=True)
    owner = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/general/appname', WithDecryption=True)
    application_name = parameter['Parameter']['Value']

    url = "https://" + fqdn

    sender = "donotreply@np-dev.pge.com"
    recipient = 'bdg3@pge.com' #event['NotificationEmail']
    configuration_set = "AED_Notifications_ConfigSet"
    template = 'S3Web_Success'
    aws_region = 'us-west-2'
    cloud_coe_recipient = 'bdg3@pge.com'
    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=aws_region)
    # Try to send the email.
    try:
        template_data = { "owner": owner, "application_name": application_name, "fqdn": fqdn, "url": url }
        response = client.send_templated_email(
        Source=sender,
        Destination={
            'ToAddresses': [
                recipient
            ],
            'CcAddresses': [
                cloud_coe_recipient
            ],
            'BccAddresses': [
            ]
        },
        ConfigurationSetName=configuration_set,
        Template=template,
        TemplateData=json.dumps(template_data)
    )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:")
        print(response['MessageId'])
    return
