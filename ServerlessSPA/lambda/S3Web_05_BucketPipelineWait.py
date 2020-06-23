from __future__ import print_function
import json
import boto3
import botocore
import time

# Description: A Python 3.x Lambda function, waits for completion of a specified CloudFormation stack.
# Author: Billy Glenn
# Version: 2019-05-18
# Input parameters: The function expects the name of the stack in question e.g. "BillyApp-cert"

# ==============================================================================
#
# Setup Session(s)
#
# ==============================================================================

session = boto3.Session(region_name='us-east-1')
ssm = session.client('ssm', region_name='us-east-1')
client = boto3.client('cloudformation', region_name='us-east-1')
waiter = client.get_waiter('stack_create_complete')

# ==============================================================================
#
# lambda_handler()
#
# ==============================================================================
def lambda_handler(event, context):
    print("Start waiting for S3Web Pipeline Stack to Complete")

    # Parse input values from event
    pAppName = event['pAppName']
    
# ==============================================================================
#
# Retrieve Parameter Store Values
# 
# ==============================================================================
    print("Reading Parameters")
    parameter = ssm.get_parameter(Name='/S3Web/' + pAppName + '/S3WebStack', WithDecryption=True)
    s3webstack = parameter['Parameter']['Value']
    print("Invoking waiter on " + s3webstack)

    waiter.wait(StackName=s3webstack)