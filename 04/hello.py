print("this verifies that hello .py can run from jenkins")

if __name__ == '__main__':
    '''
    Sample usage:
    <filename.py>  path_to_master_csv s3_bucket_uri sqs_url
    name 
    '''
    # step 1: split the csv into (what we will call) chunks
    # step 2: upload each chunk to S3. Store s3 uri of each chunk.
    # step 3: for each chunk_s3_uri, send a message to SQS