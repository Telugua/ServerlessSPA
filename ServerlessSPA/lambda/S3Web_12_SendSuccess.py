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
# Setup Session(s)
#
# ==============================================================================

session = boto3.Session(region_name='us-east-1')
ssm = session.client('ssm', region_name='us-east-1')


def lambda_handler(event, context):

    # Parse input values from event
    pAppName = event['pAppName']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/FQDN', WithDecryption=True)
    fqdn = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/Owner', WithDecryption=True)
    owner = parameter['Parameter']['Value']

    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/AppName', WithDecryption=True)
    application_name = parameter['Parameter']['Value']

    url = "https://" + fqdn

    sender = "donotreply@np-dev.pge.com"
    recipient = owner
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
