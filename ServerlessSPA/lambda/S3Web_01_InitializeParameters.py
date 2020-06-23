from __future__ import print_function
import json
import boto3
import botocore
import time


# ==============================================================================
#
# lambda_handler()
#
# ==============================================================================
def lambda_handler(event, context):

    # Parse input values from event
    pAppName = event['pAppName']
    pBuildSpec = event['pBuildSpec']
    pAppID = event['pAppId']
    pEnv = event['pEnv']
    pCFNOwner = event['pCFNOwner']
    pCertificateSubject = event['pCertificateSubject']
    pRoute53AssumedRoleArn = event['pRoute53AssumedRoleArn']
    pRoute53PublicHostedZoneId = event['pRoute53PublicHostedZoneId']
    pRoute53PrivateHostedZoneId = event['pRoute53PrivateHostedZoneId']
    pRoute53AssumedRoleArn = event['pRoute53AssumedRoleArn']
    pGitHubAccount = event['pGitHubAccount']
    pGitHubRepo = event['pGitHubRepo']
    pGitHubRepoBranch = event['pGitHubRepoBranch']
    # pNotify = event['NotificationEmail']
    # pOrg = event['BusinessOrganization']
    # pOrder = event['OrderNumber']
    # pProjectName = event['ProjectName']
    # pRole = event['AssetRole']

    # Establish Systems Manager Session to access Parameter Store
    session = boto3.Session(region_name='us-east-1')
    ssm = session.client('ssm', region_name='us-east-1')

    try:
        print("----+ Create Parameter Store Namespace  /S3Web/" + pAppName + "/ -------------------------------------------------------")

        ssm.put_parameter(Name='/S3Web/' + pAppName + '/AppName', Value=pAppName, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/BuildSpec', Value=pBuildSpec, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/AppId', Value=pAppID, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/Environment', Value=pEnv, Type='String', Overwrite=True)
    #    ssm.put_parameter(Name='/general/notify', Value=pNotify, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/Owner', Value=pCFNOwner, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/FQDN', Value=pCertificateSubject, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/Route53Role', Value=pRoute53AssumedRoleArn, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/Route53PublicHostedZone', Value=pRoute53PublicHostedZoneId, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/Route53PrivateHostedZone', Value=pRoute53PrivateHostedZoneId, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/Route53AssumedRoleARN', Value=pRoute53AssumedRoleArn, Type='String', Overwrite=True)        
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/GithubAccount', Value=pGitHubAccount, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/GithubRepo', Value=pGitHubRepo, Type='String', Overwrite=True)
        ssm.put_parameter(Name='/S3Web/' + pAppName + '/GithubRepoBranch', Value=pGitHubRepoBranch, Type='String', Overwrite=True)

        # ssm.put_parameter(Name='/general/org', Value=pOrg, Type='String', Overwrite=True)
        # ssm.put_parameter(Name='/general/order', Value=pOrder, Type='String', Overwrite=True)
        # ssm.put_parameter(Name='/general/project', Value=pProjectName, Type='String', Overwrite=True)
        # ssm.put_parameter(Name='/general/role', Value=pRole, Type='String', Overwrite=True)

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

    print("----+ Generate and Store Referer Secret /S3Web/" + pAppName + "/Cloudfront-Referer ------------------------------------")

    smclient = boto3.client('secretsmanager', region_name='us-east-1')
    randomresponse = smclient.get_random_password(
        PasswordLength=30,
        ExcludeNumbers=False,
        ExcludePunctuation=True,
        ExcludeUppercase=False,
        ExcludeLowercase=False,
        IncludeSpace=False,
        RequireEachIncludedType=True
    )
    # Extract JUST the password from the response object:
    randompassword = randomresponse['RandomPassword']

    try:
        secname = '/S3Web/' + pAppName + '/Cloudfront-Referer'
        response = smclient.create_secret(
            Name= secname,
            Description='Referer string for S3Web product',
            SecretString=randompassword,
            Tags = [ 
                { 'Key': 'AppID', 'Value': pAppID },
                { 'Key': 'Environment', 'Value': pEnv },
                { 'Key': 'Notify', 'Value': pCFNOwner },
                { 'Key': 'Order', 'Value': "00000000" },
                { 'Key': 'Org', 'Value': "CCOE" },
                { 'Key': 'Owner', 'Value': pCFNOwner },
                { 'Key': 'AppName', 'Value': pAppName }
                ]
            )

    except botocore.exceptions.ClientError as e:
            print(e)
            payload = {
                "status":False,
                "payload": {
                    "AppName": pAppName,
                    "payload": "create_secret() failed."
                }
            }
            return payload