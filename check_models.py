import boto3
import os

# Set credentials
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'YOUR_AWS_ACCESS_KEY_ID'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'YOUR_AWS_SECRET_ACCESS_KEY'

bedrock = boto3.client('bedrock', region_name='us-east-1')

try:
    response = bedrock.list_foundation_models()
    print("Available models in your account:\n")
    for model in response['modelSummaries']:
        print(f"- {model['modelId']} ({model['modelName']})")
except Exception as e:
    print(f"Error: {e}")
