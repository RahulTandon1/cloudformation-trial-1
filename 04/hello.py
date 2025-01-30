import sys
import boto3

if __name__ == '__main__':
    '''
    Sample usage:
    <filename.py> test_unique_id path_to_master_csv path_to_jmx s3_bucket_uri sqs_url
    name 
    '''
    num_args = len(sys.argv)
    if num_args < 6:
        print(sys.argv)
        sys.exit('Not enough arguments were passed')

    test_unique_id, local_path_to_csv, local_path_to_jmx, s3_bucket, sqs_url = sys.argv[1:]
    print('test_unique_id', test_unique_id) 
    print('local_path_to_csv', local_path_to_csv)
    print('local_path_to_jmx', local_path_to_jmx) 
    print('s3_bucket', s3_bucket)
    print('sqs_url', sqs_url)
     
    # ==============================================================================
    # step 0: push JMX and CSV to S3 for ability to recreate test later if required
    # ==============================================================================
    s3_key_of_master_csv=f"{test_unique_id}/master_data.csv"
    s3_key_of_jmx=f"{test_unique_id}/test_plan.jmx"
    
    s3 = boto3.client('s3')
    s3.upload_file(local_path_to_csv, s3_bucket, s3_key_of_master_csv)
    s3.upload_file(local_path_to_jmx, s3_bucket, s3_key_of_jmx)
    print("Completed Step 0: Upload master CSV & JMX to S3")

    # ==============================================================================
    # step 1: split the csv into (what we will call) chunks
    # step 2: upload each chunk to S3. Store s3 uri of each chunk.
    # step 3: for each chunk_s3_uri, send a message to SQS