pipeline {
    agent any
    
    parameters {
        stashedFile 'test_data'
        stashedFile 'jmx_file'
        string(
            name: 'LOAD_TEST_S3_BUCKET', 
            defaultValue: 'v1-edfora-load-test-reports', 
            description: 's3 bucket for storing input CSV & JMX files + output reports'
        )
    }
    stages {
        stage('Moving input files') {
            steps {
                // to do: throw error if input files are not present
                withFileParameter('test_data') {
                    sh 'mv $test_data test_data.csv'
                }
                withFileParameter('jmx_file') {
                    sh 'mv $jmx_file test_plan.jmx'
                }
                fileExists 'test_data.csv'
                fileExists 'test_plan.jmx'
            }
        }
        
        stage('Upload to S3 & Configure EC2 instances') {
            steps {
                git branch: 'main', url: 'https://github.com/RahulTandon1/cloudformation-trial-1'
                sh '''alias aws="/usr/local/bin/aws"
                aws --version
                aws s3 ls $LOAD_TEST_S3_BUCKET
                # will throw error & exit if the bucket does not exist
                
                ls -al ./

                current_date_time=$(date '+%Y/%d-%b-%Hh:%Mm:%Ss') # example 2025/20-Jan-12h:33m:12s
                s3_path_for_test_data="s3://$LOAD_TEST_S3_BUCKET/$current_date_time/test_data.csv"
                s3_path_for_jmx="s3://$LOAD_TEST_S3_BUCKET/$current_date_time/test_plan.jmx"
                
                aws s3 cp test_data.csv $s3_path_for_test_data
                
                # aws s3 ls bhai_ye_exist_kari_toh_main_express_ho_jaunga
                
                aws s3 cp test_plan.jmx $s3_path_for_jmx                

                aws cloudformation create-stack \
                    --stack-name stack-117 \
                    --template-body file://v1.yaml \
                    --region ap-south-1 \
                    --parameters \
                        ParameterKey=S3URLOfCsv,ParameterValue="s3://v1-edfora-load-test-reports/2025/20-Jan-12h:41m:44s/test_data.csv" \
                        ParameterKey=S3URLOfJMX,ParameterValue="s3://v1-edfora-load-test-reports/2025/20-Jan-12h:41m:44s/test_plan.jmx" \
                    --output text
                '''
            }
        }
        stage('Wait on completion of load test') {
            options {
                timeout(time: 10, unit: "MINUTES")
                // timeout(time: 2, unit: "HOURS") // TODO: for actual pipeline (could parameterize)
            }
            steps {
                script {
                    hook = registerWebhook()
                    callbackURL = hook.url
                    
                    // Call a remote system to start execution, passing the callback url
                    //sh "curl -X POST -H 'Content-Type: application/json' -d '{\"callback\":\"${callbackURL}"}' http://httpbin.org/post"

                    echo "Waiting for POST to ${callbackURL}"
                    data = waitForWebhook hook
                    
                    echo "Webhook called with data: ${data}"
                    // def jsonSlurper = new JsonSlurper()
                    // echo "Class of object is ${object.getClass()}"
                    def object = readJSON text: data
                    // data.S3_URL_of_test_report will contain the S3 information to the pull JMX report
                }
            }
        }
        stage('Delete provisioned infrastructure') {
            steps {
                sh '''echo 'TODO: complete this step'
                aws cloudformation delete-stack \
                    --stack-name arn:aws:cloudformation:ap-south-1:577638381290:stack/stack-117/3c5ca530-d71e-11ef-be7b-0685e1d5018b \
                    --region ap-south-1
                '''
            }
            // will not delete the dedicated S3 bucket for reports
            // TODO: should we delete the csv and jmx uploaded?
            // delete the cloudformation stack
        }
        // stage('Create CloudFormation Stack') {
        //     steps {
        //         script {
        //             def stackName = 'jenkins-created-stack-1'
        //             def templateFile = '/Users/rahultandon/dev/trying-stuff/l-aws/cloudformation-trial-1'
                    
        //             // Create or update the CloudFormation stack
        //             // cfnUpdate(stack: stackName, file: templateFile, params: [], timeoutInMinutes: 30)
        //             cfnUpdate(stack: stackName, file: templateFile, params: [], timeoutInMinutes: 30)
        //         }
        //     }
        // }
        
        // stage('Echo ARNs') {
        //     steps {
        //         script {
        //             def stackName = 'my-stack-name'
                    
        //             // Get stack outputs
        //             def outputs = cfnDescribe(stack: stackName)
                    
        //             // Echo ARNs or other outputs
        //             outputs.each { key, value ->
        //                 echo "Output ${key}: ${value}"
        //             }
        //         }
        //     }
        // }
    }
}
