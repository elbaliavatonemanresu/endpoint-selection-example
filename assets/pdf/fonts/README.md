# Fonts

## PDF Font Requirements

The CTTI Endpoint Selection Facilitator uses system fonts for PDF generation to ensure portability and avoid licensing issues.

### Primary Font Family
- **Open Sans** (if available on system)
- Fallback: **Arial**
- Fallback: **Helvetica Neue**
- Final fallback: **sans-serif**

### Font Usage by Section

#### Cover Page
- Title: Bold, XL (2rem equivalent, ~32pt)
- Metadata: Regular, MD (1.125rem equivalent, ~18pt)

#### Section Headers
- Semibold, LG (1.5rem equivalent, ~24pt)

#### Body Text
- Regular, SM (1rem equivalent, ~16pt)

#### Tables & Charts
- Regular/Semibold, SM/XS (1rem/0.875rem equivalent, ~16pt/14pt)

#### Metadata Footer
- Light, XS (0.875rem equivalent, ~14pt)

### Font Weights
- Light: 300
- Normal: 400
- Semibold: 600
- Bold: 700

### Notes
- All fonts are loaded from the system font directory
- No custom font files are required or included
- PyMuPDF (fitz) handles font rendering using system fonts
- If a preferred font is unavailable, the next in the fallback chain is used automatically
