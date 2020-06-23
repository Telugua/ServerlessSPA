from __future__ import print_function
import json
import boto3
import botocore
import time

step_id = 1

# ==============================================================================
#
# lambda_handler()
#
# ==============================================================================
def lambda_handler(event, context):

    resume_step = event['ResumeStep']
    account_id = event['AccountId']

    # Check if this step has been done already.
    if resume_step > step_id:
        print("Resume from Step {}. Skip this step.".format(resume_step))
        if len(account_id) != 12:
            print("Created account ID is needed.")
            payload = '{"status":"False", "payload": "Created account ID is needed."}'
            return json.loads(payload)
        payload = '{"status":"True", "payload": "%s"}' % account_id
        return json.loads(payload)


    account_name = event['AccountName']
    account_email = event['AccountEmail']

    role_arn = event['CreateMoveAccountRoleArn']

    account_role = 'OrganizationAccountAccessRole'

    print('account_name is {0}'.format(account_name))
    print('account_email is {0}'.format(account_email))
    print('account_role is {0}'.format(account_role))
    print('role_arn is {0}'.format(role_arn))

    # --------------------------------------------------------------------------
    # ---------- Check input account name duplication
    # --------------------------------------------------------------------------
    ssm = boto3.client('ssm')

    parameter = ssm.get_parameter(Name='/Account/MemberAccount/NameList', WithDecryption=True)
    account_name_list = parameter['Parameter']['Value']
    print(account_name_list)

    if account_name in account_name_list:
        print("Input account name already exists.")
        payload = '{"status":"False", "payload": "Input account name already exists."}'
        return json.loads(payload)

    # --------------------------------------------------------------------------
    # ---------- Check input email address duplication
    # --------------------------------------------------------------------------
    parameter = ssm.get_parameter(Name='/Account/MemberAccount/EmailList', WithDecryption=True)
    account_email_list = parameter['Parameter']['Value']
    account_email_list = account_email_list.strip()
    print(account_email_list)

    if account_email in account_email_list:
        print("Input email address already exists.")
        payload = '{"status":"False", "payload": "Input email address already exists."}'
        return json.loads(payload)

    # --------------------------------------------------------------------------
    # ---------- Create account
    # --------------------------------------------------------------------------
    credentials = assume_role(role_arn)
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    client = session.client('organizations')

    try:
        create_account_response = client.create_account(Email=account_email,
                                                        AccountName=account_name,
                                                        RoleName=account_role,
                                                        IamUserAccessToBilling='DENY')
    except botocore.exceptions.ClientError as e:
        print(e)
        payload = '{"status":"False", "payload": %s}' % e
        return  json.loads(payload)

    time.sleep(10)

    account_status = 'IN_PROGRESS'
    while account_status == 'IN_PROGRESS':
        print('before calling describe_create_account_status')
        create_account_status_response = client.describe_create_account_status(CreateAccountRequestId=create_account_response.get('CreateAccountStatus').get('Id'))
        account_status = create_account_status_response.get('CreateAccountStatus').get('State')

    if account_status == 'SUCCEEDED':
        print('before calling describe_create_account_status')
        account_id = create_account_status_response.get('CreateAccountStatus').get('AccountId')
        payload = '{"status":"True", "payload": "%s"}' % account_id

        ssm = boto3.client('ssm')
        parameter = ssm.get_parameter(Name='/Account/MemberAccount/IdList', WithDecryption=True)
        account_id_list = parameter['Parameter']['Value']
        print(account_id_list)

        account_id_list = account_id_list.strip()
        if account_id_list == "":
            account_id_list =  account_id
        else:
            account_id_list = account_id_list + ',' + account_id


        print(account_id_list)
        print('---------- Before parameter store account_id_list insertion')
        response = ssm.put_parameter(Name='/Account/MemberAccount/IdList', Value=account_id_list, Type='StringList', Overwrite=True)
        print(response)

        print('----+----+ Copy /StackSets/NameList to /StackSets/NameListWorkNeeded')
        parameter = ssm.get_parameter(Name='/StackSets/NameList', WithDecryption=True)
        stack_set_name_list = parameter['Parameter']['Value']

        response = ssm.put_parameter(
            Name='/StackSets/NameListWorkNeeded',
            Value=stack_set_name_list,
            Type='StringList',
            Overwrite=True
        )
        print(response)

        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            payload = '{"status":"False", "payload": %s}' % response
            return json.loads(payload)

        account_name_list = account_name_list.strip()
        if account_name_list == "":
            account_name_list =  account_name
        else:
            account_name_list = account_name_list + ',' + account_name

        print(account_name_list)
        print('---------- Before parameter store account_name_list insertion')
        response = ssm.put_parameter(Name='/Account/MemberAccount/NameList', Value=account_name_list, Type='StringList', Overwrite=True)
        print(response)

        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            payload = '{"status":"False", "payload": %s}' % response
            return json.loads(payload)


        account_email_list = account_email_list.strip()
        if account_email_list == "":
            account_email_list =  account_email
        else:
            account_email_list = account_email_list + ',' + account_email

        print(account_email_list)
        print('---------- Before parameter store account_email_list insertion')
        response = ssm.put_parameter(Name='/Account/MemberAccount/EmailList', Value=account_email_list, Type='StringList', Overwrite=True)
        print(response)

        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            payload = '{"status":"False", "payload": %s}' % response
            return json.loads(payload)

    elif account_status == 'FAILED':
        payload = '{"status":"False", "payload": "Account Creation Failed"}'

    return json.loads(payload)


# ==============================================================================
#
# assume_role()
#
# ==============================================================================
def assume_role(role_arn):
    sts_client = boto3.client('sts')
    assumed_role_object = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName='foundation',
    )
    credentials = assumed_role_object['Credentials']

    return credentials