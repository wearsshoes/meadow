"""Module for analyzing PDFs using Claude API"""

import json
import os
import base64
import hashlib
import pymupdf  # PyMuPDF
from anthropic import Anthropic, AnthropicError

class PDFAnalyzer:
    """Class for analyzing PDF documents using Claude API and extracting structured information."""
    def __init__(self):
        # Use config API key if available, otherwise fall back to environment variable
        api_key = None
        self.app_dir = os.path.join(os.path.expanduser('~/Library/Application Support/Meadow'))
        config_path = os.path.join(self.app_dir, 'config', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get('anthropic_api_key')
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()

    def analyze_pdf(self, pdf_base64):
        """Analyze PDF using Claude API. Returns tuple of (analysis_results, page_images)"""
        print("[DEBUG] Received pdf to analyze.")
        try:
            # Decode base64 PDF
            pdf_bytes = base64.b64decode(pdf_base64)

            # Open PDF with PyMuPDF
            doc = pymupdf.Document(stream=pdf_bytes, filetype="pdf")
            total_pages = doc.page_count
            print(f"[DEBUG] Total pages: {total_pages}")

            # Extract text and analyze each page
            analysis_results = []
            page_images = []

            for page_num in range(total_pages):
                page = doc[page_num]

                # Convert page to image for OCR
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                page_images.append(img_data)

                img_base64 = base64.b64encode(img_data).decode()
                print(f"[DEBUG] Converted {page_num + 1} of {total_pages}. Sending to Claude")

                prompt = f"""
Analyze this page (Page {page_num + 1} of {total_pages}) from the PDF document.

Please:
1. Summarize any typed text present
2. Extract and transcribe any handwritten notes
3. Note any highlighted sections
4. Organize the information in markdown format

Return your analysis in the following structure:
# Page {page_num + 1}
## Text Summary
[Your summary of typed text]

## Handwritten Notes
[Transcription of any handwritten notes]

## Highlights
[Description of highlighted sections]

---
"""

                message = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1500,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }]
                )

                analysis_results.append(message.content[0].text)

            # Return both analysis results and page images
            return analysis_results, page_images

        except (AnthropicError) as e:
            raise RuntimeError(f"Error analyzing PDF: {str(e)}") from e
