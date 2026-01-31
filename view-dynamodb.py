#!/usr/bin/env python3
"""
Script to view LocalStack DynamoDB table contents.
Usage: python3 view-dynamodb.py
"""

import boto3
import json
from datetime import datetime

# Connect to LocalStack DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

table = dynamodb.Table('UsersTable')

# Scan the table
response = table.scan()
items = response['Items']

print(f"\n{'='*80}")
print(f"LocalStack DynamoDB - UsersTable")
print(f"{'='*80}")
print(f"Total Users: {len(items)}\n")

if items:
    for i, item in enumerate(items, 1):
        print(f"User {i}:")
        print(f"  Email: {item.get('email', 'N/A')}")
        print(f"  Name: {item.get('name', 'N/A')}")
        print(f"  Password Hash: {item.get('password_hash', 'N/A')[:20]}...")
        print(f"  Created At: {item.get('created_at', 'N/A')}")
        print()
else:
    print("No users found in the table.\n")

print(f"{'='*80}\n")

# Pretty print full JSON
print("Full JSON Output:")
print(json.dumps(items, indent=2, default=str))
