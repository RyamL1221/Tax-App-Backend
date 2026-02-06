#!/bin/bash

echo "=== Testing PDF Field Mapping Fix ==="
echo ""

# Test with sam local invoke
echo "1. Testing Lambda function with sam local invoke..."
sam local invoke GenerateTaxDocumentFunction \
  --event test-event-tax-doc.json \
  --env-vars env.json \
  --docker-network tax-app-network \
  2>&1 | grep -E "(statusCode|jobId|outputKey)" | tail -3

echo ""
echo "2. Downloading generated PDF from S3..."

# Extract the job ID from the last invocation (we'll use a known one for now)
JOB_ID="60873cd3-035b-4a53-b395-d68aa176eed2"
USER_ID="test-user-123"

aws --endpoint-url=http://localhost:4566 s3 cp \
  s3://tax-app-documents/outputs/${USER_ID}/${JOB_ID}/form-1099-DIV.pdf \
  test-output-1099-DIV.pdf \
  2>&1 | grep -v "Completed"

echo ""
echo "3. Verifying PDF field values..."

python3 << 'EOF'
from pypdf import PdfReader

reader = PdfReader('test-output-1099-DIV.pdf')
fields = reader.get_fields()

# Check the specific fields we populated
test_fields = {
    'topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]': 'payerName',
    'topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]': 'payerTIN',
    'topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]': 'recipientName',
    'topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]': 'recipientTIN',
    'topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]': 'totalOrdinaryDividends',
    'topmostSubform[0].Copy1[0].RghtCol[0].f2_10[0]': 'qualifiedDividends',
}

all_populated = True
for pdf_field, api_field in test_fields.items():
    if pdf_field in fields:
        field = fields[pdf_field]
        value = field.get('/V', None)
        if value:
            print(f"✓ {api_field}: {value}")
        else:
            print(f"✗ {api_field}: NO VALUE")
            all_populated = False
    else:
        print(f"✗ {api_field}: FIELD NOT FOUND")
        all_populated = False

print()
if all_populated:
    print("✅ SUCCESS: All fields are populated correctly!")
else:
    print("❌ FAILURE: Some fields are missing or empty")
    exit(1)
EOF

echo ""
echo "=== Test Complete ==="
