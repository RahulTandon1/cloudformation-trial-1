import sys
import boto3
import csv
import tempfile


if __name__ == '__main__':
    '''
    Sample usage:
    <filename.py> test_unique_id path_to_master_csv path_to_jmx s3_bucket_uri sqs_url
    name 
    '''
    num_args = len(sys.argv)
    if num_args < 7:
        print(sys.argv)
        sys.exit('Not enough arguments were passed')

    num_workers, test_unique_id, local_path_to_csv, local_path_to_jmx, s3_bucket, sqs_url = sys.argv[1:]
    print('num_workers', num_workers)
    print('test_unique_id', test_unique_id) 
    print('local_path_to_csv', local_path_to_csv)
    print('local_path_to_jmx', local_path_to_jmx) 
    print('s3_bucket', s3_bucket)
    print('sqs_url', sqs_url)
    num_workers = int(num_workers) 
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
    # ==============================================================================

    # Read and split the CSV file 
    with open(local_path_to_csv, "r") as csv_file:
        reader = list(csv.reader(csv_file))
        header_line = reader[0]  # Extract headers
        rows = reader[1:]    # Extract data rows
    num_rows = len(rows)
    
    print("nums_workers", num_workers)
    print("num_rows", num_rows)
    print("first 5 lines of CSV data", rows[:5])
    
    if num_rows < num_workers:
        sys.exit('Number of rows in CSV is less than number of workers to distribute them across')

    
    chunk_size = num_rows // num_workers
    num_rows_left = num_rows % num_workers
    
    # paths of temporary files for each worker
    # temp_dir_prefix = f"/tmp/{test_unique_id}"
    temp_dir_manager_obj = tempfile.TemporaryDirectory() # remember to call .cleanup() once done
    temp_dir_prefix = temp_dir_manager_obj.name
    paths_to_chunk_csvs = [f"{temp_dir_prefix}/{worker_index}.csv" for worker_index in range(num_workers)]
    
    # allocate rows[0, (chunk_size * num_workers) ] across num_workers
    # inclusive of 0, exclusive of end index
    # this will leave <num_rows_left> unassigned rows at the end
    # there indices will be rows[(chunk_size * num_workers), num_rows]
    for worker_index in range(num_workers):
        # find the chunk range for this worker
        from_index = worker_index * chunk_size # inclusive of this index
        to_index = (worker_index + 1) * chunk_size # exclusive of this index
        chunk = rows[ from_index : from_index]
        
        temp_output_file = paths_to_chunk_csvs[ worker_index ]
        # Write chunk to a NEW temporary CSV file
        # Will overwrite any file previously located at temp_output_file
        with open(temp_output_file, "w", newline="") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(header_line)  # Write header line
            writer.writerows(chunk)   # Write rows

    # distribute the rows[(chunk_size * num_workers), num_rows]
    # starting at the first worker
    remaining_rows = rows[(chunk_size * num_workers) : num_rows]
    for index, row in enumerate(remaining_rows):
        temp_output_file = paths_to_chunk_csvs[ worker_index ]
        
        # append to previous temp file
        with open(temp_output_file, "a", newline="") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(row)
    
    # now all rows from the master CSV have been distributed across files in <paths_to_chunk_csvs>
    print(f"Completed Step 1: CSVs have been split into chunk CSV files: \n {paths_to_chunk_csvs}")
    
    # ==============================================================================
    # step 2: upload each chunk to S3. Store s3 uri of each chunk.
    # ==============================================================================
    list_of_s3_csv_uris = []
    for index, path_to_chunk_csv in enumerate(paths_to_chunk_csvs):
        s3_key_upload_key = f"{test_unique_id}/tmp/{index + 1}.csv"
        s3.upload_file(path_to_chunk_csv, s3_bucket, s3_key_upload_key)
        list_of_s3_csv_uris.append(f'{s3_bucket}/{s3_key_upload_key}')
    
    print(f"Completed Step 2: CSV chunks have been uploaded to S3: \n {list_of_s3_csv_uris} \n")
    
    temp_dir_manager_obj.cleanup() # cleanup the temp dir created in step 1
    # ==============================================================================
    
    # step 3: for each chunk_s3_uri, send a message to SQS
