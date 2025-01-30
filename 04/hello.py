import sys

if __name__ == '__main__':
    '''
    Sample usage:
    <filename.py> test_unique_id path_to_master_csv path_to_jmx s3_bucket_uri sqs_url
    name 
    '''
    num_args = len(sys.argv)
    if num_args < 6:
        sys.exit('Not enough arguments were passed')

    test_unique_id, local_path_to_csv, local_path_to_jmx, s3_bucket, sqs_url = sys.argv[1:]
    print('test_unique_id', test_unique_id) 
    print('local_path_to_csv', local_path_to_csv)
    print('local_path_to_jmx', local_path_to_jmx) 
    print('s3_bucket', s3_bucket)
    print('sqs_url', sqs_url)
     
    # step 1: split the csv into (what we will call) chunks
    # step 2: upload each chunk to S3. Store s3 uri of each chunk.
    # step 3: for each chunk_s3_uri, send a message to SQS