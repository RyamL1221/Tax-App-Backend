# Next Test - PyMuPDF v2 with NeedAppearances

## ✅ TEST THIS: pymupdf-v2-1099-DIV.pdf

### Changes in This Version
1. Added explicit field flag manipulation to ensure fields aren't hidden
2. Attempted to set NeedAppearances flag in the PDF catalog
3. Double update() call after setting field values

### Expected Result
Field values should be visible when you open the PDF.

### Test Data
- payerName: Test Payer Inc
- payerTIN: 12-3456789
- recipientName: John Doe
- recipientTIN: 987-65-4321
- totalOrdinaryDividends: 1500.0
- qualifiedDividends: 1200.0

**Please open `pymupdf-v2-1099-DIV.pdf` and let me know if the fields are visible!**

If this still doesn't work, I have one more approach to try with PyMuPDF that involves manually drawing the text on the PDF.
