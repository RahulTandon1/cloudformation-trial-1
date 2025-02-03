'''
This is a script to run on each EC2 instance.

Sample usage: <filename.py> <SQS Queue URL> <msg group id to filter by> <absolute path to write to> [optional: region]

Purpose:
- given an SQS URL, download/pulls message until it receives a single msg with MessageGroupId == msg_group_id
- extract the S3 URL from it
- download the S3 file to an absolute path
- delete the message from SQS
'''

import sys
import boto3
from urllib.parse import urlparse
from pathlib import Path


REGION = 'ap-south-1'
def download_single_message_from_queue(sqs_url, msg_group_id, max_attempts=10):
    sqs = boto3.client('sqs', region_name=REGION)
    try:
        for attempt_number in range(1, max_attempts + 1):
            print(f'[ download single message ] attempt #{attempt_number}')
            
            response = sqs.receive_message(
                QueueUrl=sqs_url,
                MaxNumberOfMessages=1,
                VisibilityTimeout=60, # unit is seconds
                # TODO: investigate why I'm unable to use a newer version
                # MessageSystemAttributeNames = ['MessageGroupId'] # we also want the MessageGroupId
                AttributeNames = ['MessageGroupId'] # we also want the MessageGroupId
            )
            
            # ensure the msg if from the required msg_group_id
            msgs = response.get('Messages', None)
            if msgs == None or len(msgs) == 0:
                sys.exit(f'Response had no messages: \n {response}')
            message = msgs[0]
            
            group_id_of_received_msg = message['Attributes']['MessageGroupId']
            if group_id_of_received_msg == msg_group_id:
                return message
            
            print(f'msg group ID of message ( {group_id_of_received_msg} ) is not {msg_group_id}')
            # put the message back into queue by setting its VisibilityTimeout to 0
            response = sqs.change_message_visibility(
                QueueUrl=sqs_url,
                ReceiptHandle=message['ReceiptHandle'],
                VisibilityTimeout=0
            )
    except Exception as e:
        sys.exit(f'Got an exception when receiving message from SQS queue {sqs_url}: \n{e}')


if __name__ == '__main__':
    args = sys.argv
    if len(args) < 4:
        sys.exit(f'Not enough arguments were passed. Received: {args}')
    
    sqs_url = args[1]
    msg_group_id = args[2]
    path_to_file_location = args[3]

    sqs = boto3.client('sqs', region_name=REGION)
    
    # ============ step: download a single message ============
    message = download_single_message_from_queue(sqs_url, msg_group_id)
    print(f'Completed Step 1: retrieve msg from SQS queue')

    
    # ============ step: download S3 file to absolute file path ============
    # extract S3 url
    receipt_handle = message['ReceiptHandle']
    s3_uri_of_file = message['Body']

    s3 = boto3.client('s3', region_name=REGION)

    # extract bucket name & url from S3 URI (https://stackoverflow.com/questions/42641315/s3-urls-get-bucket-name-and-path)
    temp_obj = urlparse(s3_uri_of_file)
    bucket_name, bucket_key = temp_obj.netloc, temp_obj.path.lstrip('/') 
    try:
        # path_to_file_location MIGHT contain nested dirs. Example: ./dir1/dir2/file.jmx
        # create the nested dirs if not present already
        split_result = path_to_file_location.rsplit('/', 1)
        if len(split_result) > 1: # if it contains nested dirs
            path_of_prefix_dir = Path( split_result[0] )
            path_of_prefix_dir.mkdir(parents=True, exist_ok=True)
        
        s3.download_file(bucket_name, bucket_key, path_to_file_location)
    except Exception as e:
        sys.exit(f'Got an exception when downloading file from S3 {bucket_name}/{bucket_key} to {path_to_file_location}:\n {e}')
    
    print(f'Completed Step 2: downloaded file from S3 URI {s3_uri_of_file} to {path_to_file_location}')
    
    
    # ============ step: delete the message from SQS ============
    try:
        response = sqs.delete_message(
            QueueUrl=sqs_url,
            ReceiptHandle=receipt_handle
        )
    except Exception as e:
        sys.exit(f'Got an exception when deleting msg from SQS queue {sqs_url}:\n {e}')
    
    print(f'Completed Step 3: delete message from SQS queue {sqs_url}')






