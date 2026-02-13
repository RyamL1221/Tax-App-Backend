#!/usr/bin/env python3
"""
Upload PDF template to LocalStack S3 bucket.

This script uploads the 1099-DIV template to the tax-app-documents bucket
in LocalStack, bypassing the awslocal shebang issue.
"""

import boto3
import sys
import os

def upload_template():
    """Upload 1099-DIV template to LocalStack S3."""
    
    # Configuration
    bucket_name = 'tax-app-documents'
    local_file = 'samples/1099-DIV.pdf'
    s3_key = 'templates/irs/1099-DIV.pdf'
    endpoint_url = 'http://localhost:4566'
    region = 'us-east-1'
    
    # Check if file exists
    if not os.path.exists(local_file):
        print(f"❌ Error: File not found: {local_file}")
        sys.exit(1)
    
    try:
        # Create S3 client
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        # Upload file
        print(f"📤 Uploading {local_file} to s3://{bucket_name}/{s3_key}...")
        s3.upload_file(local_file, bucket_name, s3_key)
        
        print(f"✅ Upload successful!")
        print(f"\nFile location: s3://{bucket_name}/{s3_key}")
        
        # Verify upload
        print("\n🔍 Verifying upload...")
        response = s3.head_object(Bucket=bucket_name, Key=s3_key)
        file_size = response['ContentLength']
        print(f"✅ File verified: {file_size} bytes")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    upload_template()
