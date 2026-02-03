Analyzing template: /Users/ryan/Library/Mobile Documents/com~apple~CloudDocs/Documents/VSCode/Tax-App-Backend/1099-DIV.pdf
Using PDF library: PyMuPDF (fitz)

================================================================================
FIELD DIMENSION ANALYSIS REPORT
================================================================================

Total fields analyzed: 140
Column types found: 3

================================================================================
COLUMN: CopyHeader
================================================================================

Field count: 11

Dimension Statistics:
  Height: min=9.00, max=10.00, avg=9.36
  Width:  min=9.00, max=28.80, avg=16.20

Recommended Font Sizes (based on minimum height):
  Default: 7.0pt
  Minimum: 6.0pt
  Maximum: 8.0pt

Sample fields (first 5):
  topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]
    Dimensions: 28.80 x 10.00
    Position: (417.60, 96.00)
    Page: 1

  topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[0]
    Dimensions: 9.00 x 9.00
    Position: (187.20, 25.00)
    Page: 1

  topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[1]
    Dimensions: 9.00 x 9.00
    Position: (244.80, 25.00)
    Page: 1

  topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]
    Dimensions: 28.80 x 10.00
    Position: (417.60, 96.00)
    Page: 2

  topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]
    Dimensions: 9.00 x 9.00
    Position: (187.20, 25.00)
    Page: 2

  ... and 6 more fields

================================================================================
COLUMN: LeftCol
================================================================================

Field count: 29

Dimension Statistics:
  Height: min=9.00, max=76.00, avg=35.48
  Width:  min=9.00, max=244.80, avg=199.40

Recommended Font Sizes (based on minimum height):
  Default: 7.0pt
  Minimum: 6.0pt
  Maximum: 8.0pt

Sample fields (first 5):
  topmostSubform[0].CopyA[0].LeftCol[0].f1_2[0]
    Dimensions: 242.05 x 76.00
    Position: (52.40, 56.00)
    Page: 1

  topmostSubform[0].CopyA[0].LeftCol[0].f1_3[0]
    Dimensions: 122.40 x 36.00
    Position: (50.40, 144.00)
    Page: 1

  topmostSubform[0].CopyA[0].LeftCol[0].f1_4[0]
    Dimensions: 122.40 x 36.00
    Position: (172.80, 144.00)
    Page: 1

  topmostSubform[0].CopyA[0].LeftCol[0].f1_5[0]
    Dimensions: 242.05 x 26.00
    Position: (52.40, 190.00)
    Page: 1

  topmostSubform[0].CopyA[0].LeftCol[0].f1_6[0]
    Dimensions: 242.05 x 26.00
    Position: (52.40, 226.00)
    Page: 1

  ... and 24 more fields

================================================================================
COLUMN: RghtCol
================================================================================

Field count: 100

Dimension Statistics:
  Height: min=9.00, max=14.00, avg=12.04
  Width:  min=9.00, max=98.05, avg=80.59

Recommended Font Sizes (based on minimum height):
  Default: 7.0pt
  Minimum: 6.0pt
  Maximum: 8.0pt

Sample fields (first 5):
  topmostSubform[0].CopyA[0].RghtCol[0].f1_9[0]
    Dimensions: 89.80 x 12.00
    Position: (305.20, 60.00)
    Page: 1

  topmostSubform[0].CopyA[0].RghtCol[0].f1_10[0]
    Dimensions: 89.80 x 12.00
    Position: (305.20, 96.00)
    Page: 1

  topmostSubform[0].CopyA[0].RghtCol[0].Box2a_ReadOrder[0].f1_11[0]
    Dimensions: 89.80 x 12.00
    Position: (305.20, 120.00)
    Page: 1

  topmostSubform[0].CopyA[0].RghtCol[0].f1_12[0]
    Dimensions: 89.80 x 12.00
    Position: (406.00, 120.00)
    Page: 1

  topmostSubform[0].CopyA[0].RghtCol[0].Box2c_ReadOrder[0].f1_13[0]
    Dimensions: 89.80 x 12.00
    Position: (305.20, 144.00)
    Page: 1

  ... and 95 more fields

================================================================================
SUMMARY RECOMMENDATIONS
================================================================================

Suggested FIELD_RENDERING_CONFIG:

FIELD_RENDERING_CONFIG = {
    'CopyHeader': {
        'default_font_size': 7.0,
        'min_font_size': 6.0,
        'max_font_size': 8.0,
    },
    'LeftCol': {
        'default_font_size': 7.0,
        'min_font_size': 6.0,
        'max_font_size': 8.0,
    },
    'RghtCol': {
        'default_font_size': 7.0,
        'min_font_size': 6.0,
        'max_font_size': 8.0,
    },
}

================================================================================
POTENTIAL RENDERING ISSUES
================================================================================

Found 104 fields with height < 13pt (may have rendering issues):

  topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]
    Height: 10.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[0]
    Height: 9.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[1]
    Height: 9.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]
    Height: 10.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]
    Height: 9.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]
    Height: 9.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]
    Height: 10.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].CopyB[0].CopyHeader[0].c2_1[0]
    Height: 9.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]
    Height: 10.00pt
    Recommended max font size: 8.0pt

  topmostSubform[0].Copy2[0].CopyHeader[0].c2_1[0]
    Height: 9.00pt
    Recommended max font size: 8.0pt

  ... and 94 more small fields

================================================================================
Analysis complete!
================================================================================
