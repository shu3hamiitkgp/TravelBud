import time
import boto3
import os

clientlogs = boto3.client('logs',
region_name= "us-east-1",
aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

def create_connection():
    """Create a connection to S3 bucket
    Returns:
        s3client: S3 client object
    """
    s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
    return s3client


# def create_connection():
    
#     """AWS connnetion using boto3
#     Returns:
#         s3client: aws client id
#     """
    
#     # write_logs("starting connection to s3")
#     s3client = boto3.client('s3',
#                         region_name='us-east-1',
#                         aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
#                         aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
#                         )
#     # write_logs("connected to s3")

#     return s3client

def write_logs(message):
    
    """Writes the logs to the cloudwatch logs
    Args:
        message (str): The message to be written to the logs
    """
    
    clientlogs.put_log_events (
    logGroupName="FinalProject",
    logStreamName="app_logs",
    logEvents=[
        {
    'timestamp' : int(time.time()* 1e3),
    'message': message,
    }
    ]
    )

def uploadfile(file_name, file_content):
    
    """Upload file to S3 bucket
    Args:
        file_name (str): Name of the file
        file_content (str): Content of the file
    """

    s3client = create_connection()
    s3client.put_object(Bucket=os.environ.get('bucket_name'), Key= 'Travelbud' +'/' + file_name , Body= file_content)

def get_object_url(bucket_name, key):
    """
    Returns a URL for the specified S3 object.

    Args:
        bucket_name (str): The name of the S3 bucket.
        key (str): The key of the S3 object.

    Returns:
        str: The URL for the S3 object.
    """
    s3 = boto3.resource('s3')
    url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
    return url