import pdfplumber
import json
import re

pdf_file = "zookout_deals.pdf.pdf"
output_file = "data/deals.json"

deals = []

with pdfplumber.open(pdf_file) as pdf:
    print(f"Reading {len(pdf.pages)} pages...")

    for page in pdf.pages:
        text = page.extract_text()

        if not text:
            continue

        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            # Skip header
            if line.startswith("N S") or "Brand Name" in line:
                continue

            # Find Zookout URL
            url_match = re.search(r"https://zookout\.com/\S+", line)

            if url_match:
                url = url_match.group()

                # Remove URL from the text
                info = line.replace(url, "").strip()

                deals.append({
                    "text": info,
                    "url": url
                })

print(f"Found {len(deals)} deals.")

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(deals, f, indent=4, ensure_ascii=False)

print("✅ deals.json created successfully!")