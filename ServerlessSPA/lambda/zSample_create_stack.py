import json
import urllib
import boto3
import botocore
import traceback
#import tempfile
from datetime import datetime
from dateutil.tz import tzutc

dfile = 's3web_input.json'
cf = None

# ==============================================================================
#
# lambda_handler()
#
# ==============================================================================
def lambda_handler(event, context):


    account_id = event['AccountId']
    if len(account_id) != 12:
        result = event['Result']
        account_id = result["payload"]["AccountId"]

    print("---------------------------------------------------------------------------")
    print('account_id is {0}.'.format(account_id))

    account_id_list = [account_id]

    ssm = boto3.client('ssm')
    s3 = boto3.client('s3')

    parameter = ssm.get_parameter(Name='/StackSets/NameListWorkNeeded', WithDecryption=True)
    stack_set_name_list = parameter['Parameter']['Value']
    stack_set_name_list = stack_set_name_list.strip() #remove blank space

    parameter = ssm.get_parameter(Name='/StackSets/BucketName', WithDecryption=True)
    bucket_name = parameter['Parameter']['Value']
    bucket_name = bucket_name.strip()


    for stack_set_name in stack_set_name_list.split(','):

        stack_set_name = stack_set_name.strip()

        print("---------------------------------------------------------------------------")
        print("---- StackSet name is {0}.".format(stack_set_name))
        print("---------------------------------------------------------------------------")


        input_file_name = stack_set_name + '-input.json'

        global dfile

        try:
            input_file = s3.get_object(Bucket=bucket_name, Key=input_file_name)["Body"].read().decode('utf-8')
        except botocore.exceptions.ClientError as e:
            print("----+ Specified input file does not exists.")
            if "Access Denied" in e.response['Error']['Message']:
                input_file_name = dfile
                print("----+----+ Use default input file which is {0}.".format(input_file_name))
                input_file = s3.get_object(Bucket=bucket_name, Key=input_file_name)["Body"].read().decode('utf-8')
            else:
                raise e


        input_file = json.loads(input_file)
        stack_parameters = input_file['StackParameters']
        capabilities = input_file['Capabilities']
        account_info = input_file['AccountInfo']

        print("input_file_name is {0}.".format(input_file_name))
        # print('Stack set template file name is {0}.'.format(template_file_name))
        print('Target regions are {0}.'.format(account_info['Regions']))
        print('S3 bucket name is {0}.'.format(bucket_name))

        template_file = ""

        global cf
        #cf = boto3.resource('cloudformation')
        cf = boto3.client('cloudformation')

        # --------------------------------------------------------------------------
        # Call stack set creation or update
        # --------------------------------------------------------------------------
        print("---------------------------------------------------------------------------")
        try:
            print("----+ Call {0}.".format("start_stack_set_update_or_create()"))
            start_stack_set_update_or_create(stack_set_name, template_file, account_info, account_id_list, stack_parameters, capabilities)
        except Exception as e:
            # If any other exceptions which we didn't expect are raised
            # then fail the job and log the exception message.
            print('start_stack_set_update_or_create() failed due to the following exception.')
            print(e)
            traceback.print_exc()
            payload = {
                "status":False,
                "payload": "start_stack_set_update_or_create() failed"
            }
            return payload


        stack_set_name_list = stack_set_name_list.split(",")
        stack_set_name_list.pop(0)

        if len(stack_set_name_list) > 0:
            stackset_exists = True
            stack_set_name_list_str = ",".join(map(str,stack_set_name_list))
            response = ssm.put_parameter(
                Name='/StackSets/NameListWorkNeeded',
                Value=stack_set_name_list_str,
                Type='StringList',
                Overwrite=True
            )
        else:
            stackset_exists = False
            response = ssm.put_parameter(
                Name='/StackSets/NameListWorkNeeded',
                Value=" ",
                Type='StringList',
                Overwrite=True
            )

        payload = {
            "status":True,
            "payload": {
                "AccountId": account_id,
                "StackSetsExists": stackset_exists
            }
        }

        return payload


# ==============================================================================
#
# start_stack_set_update_or_create()
#
# ==============================================================================
def start_stack_set_update_or_create(stack_set_name, newTemplate, account_info, account_id_list, stack_parameters, capabilities):
    print("----+----+ Run {0}.".format("start_stack_set_update_or_create()"))
    """Starts the stack set update or create process

    If the stack set exists then update, otherwise create.

    Args:
        stack_set_name: The stack set to create or update
        template: The template to create/update the stack with
        account_info: Accounts and regions to create/update the stack instances in
        account_id_list: account ID list
        stack_parameters: Stack parameters
        capabilities: Stack set IAM capabilities
    """
    if stackset_exists(stack_set_name):
        ## check if
        print("Stack {0} already exists.".format(stack_set_name))
        create_stackinstances(stack_set_name, account_id_list, stack_parameters, account_info['Regions'], account_info['OperationPreferences'])
    else:
        print("StackSet {0} does not exist. Stop here.".format(stack_set_name))
        payload = '{"status":"False", "payload": "Specified StackSet does not exist."}'
        return json.loads(payload)

    print("---------------------------------------------------------------------------")


# ==============================================================================
#
# stackset_exists()
#
# ==============================================================================
def stackset_exists(stackset):
    print("----+----+ Run {0}.".format("stackset_exists()"))
    """Check if a stack set exists or not

    Args:
        stackset: The stack set to check

    Returns:
        True or False depending on whether the stack exists

    Raises:
        Any exceptions raised .describe_stacksets() besides that
        the stack doesn't exist.

    """
    global cf
    try:
        print("----+----+----+ Call {0}.".format("cf.describe_stack_set()"))
        response=cf.describe_stack_set(StackSetName=stackset)
        for k, v in response.items():
            print("                Key: {0}, Value: {1}.".format(k,v))
        return True
    except botocore.exceptions.ClientError as e:
        if "not found" in e.response['Error']['Message']:
            return False
        else:
            raise e


# ==============================================================================
#
# create_stackinstances()
#
# ==============================================================================
def create_stackinstances(stack_set_name, account_id_list, stack_parameters, regions, preferences):
    print("----+----+ Run {0}. Stacksetname: {1}".format("create_stackinstances()", stack_set_name))
    """Starts stack instances creation

    Args:
        stack_set_name: The stack to be created
        account_id_list: The list of accounts to create the stack instances
        regions: List of regions to deploy the stack instances

    Throws:
        Exception: Any exception thrown by cf.create_stack_instances()
    """

    global cf

    for account_id in account_id_list:

        print("---------------------------------------------------------------------------")
        shouldRun = False

        for region_id in regions:
            response = stackinstance_exists(stack_set_name, account_id, region_id)
            if response.get("status") == "True":
                if response.get("payload") == "CURRENT":
                    print("----+----+----+ Instance in region {0} already exists and is CURRENT.".format(region_id))
                else:
                    shouldRun = True
            else:
                shouldRun = True
                break
        if shouldRun:
            print("----+----+----+ Call {0} for {1}.".format("cf.create_stack_instances()", account_id))
            response = cf.create_stack_instances(   StackSetName = stack_set_name,
                                                    Accounts = [account_id],
                                                    ParameterOverrides = stack_parameters,
                                                    Regions = regions,
                                                    OperationPreferences = preferences)
            print(response)
            operation_id = response['OperationId']
            print("               operation_id: {0}".format(operation_id))
            dsso_status = 'RUNNING'
            while dsso_status == 'RUNNING':
                dsso_response = cf.describe_stack_set_operation(StackSetName=stack_set_name, OperationId=operation_id)
                dsso_status = dsso_response['StackSetOperation']['Status']
        else:
            print("----+----+----+ Don't call {0} for {1}.".format("cf.create_stack_instances()", account_id))


# ==============================================================================
#
# stackinstance_exists()
#
# ==============================================================================
def stackinstance_exists(stackset, account_id, region):
    print("----+----+ Run {0}.".format("stackinstance_exists()"))
    """Check if a stack instance exists or not

    Args:
        stackset: The stack set to check
        account_id: account ID
        region: region ID

    Returns:
        True or False depending on whether the stack instance exists

    """
    global cf
    try:
        print("----+----+----+ Call {0} for account {1}, region {2}.".format("cf.describe_stack_instance()", account_id, region))
        response=cf.describe_stack_instance  (   StackSetName=stackset,
                                        StackInstanceAccount=account_id,
                                        StackInstanceRegion=region  )
        for k, v in response.items():
            print("                Key: {0}, Value: {1}.".format(k,v))
        payload = '{"status":"True", "payload":"' + response['StackInstance']['Status'] + '"}'
        print(payload)
        return json.loads(payload)
    except botocore.exceptions.ClientError as e:
        if "not found" in e.response['Error']['Message']:
            payload = '{"status":"False", "payload": "Specified Stack Instance does not exist."}'
            return json.loads(payload)
        else:
            raise e