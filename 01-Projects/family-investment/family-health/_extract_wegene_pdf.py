"""
Extract WeGene official PDF report (323MB).
Save text to _wegene_pdf_raw.txt for analysis.
"""
import sys
import time
from pathlib import Path

PDF_PATH = r"E:\Personal Files\0.家庭健康\微基金检查报告-燕.pdf"
OUT_DIR = Path(r"e:\ProjectGroup\AI\ContextStack\01-Projects\family-investment\family-health")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_TXT = OUT_DIR / "_wegene_pdf_raw.txt"

print(f"[1] Opening PDF: {PDF_PATH}", flush=True)
print(f"    File size: {Path(PDF_PATH).stat().st_size / 1024 / 1024:.1f} MB", flush=True)

t0 = time.time()
pages_text = []

try:
    import pdfplumber
    print("[2] Using pdfplumber", flush=True)
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"    Total pages: {total}", flush=True)
        for i, page in enumerate(pdf.pages):
            try:
                txt = page.extract_text() or ""
            except Exception as e:
                txt = f"[page {i+1} extract error: {e}]"
            pages_text.append(f"\n\n===== Page {i+1}/{total} =====\n{txt}")
            if (i + 1) % 20 == 0 or i + 1 == total:
                elapsed = time.time() - t0
                print(f"    [{i+1}/{total}] elapsed {elapsed:.1f}s", flush=True)
except Exception as e:
    print(f"[!] pdfplumber failed: {e}", flush=True)
    print("[2-fallback] Using pypdf", flush=True)
    import pypdf
    reader = pypdf.PdfReader(PDF_PATH)
    total = len(reader.pages)
    print(f"    Total pages: {total}", flush=True)
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception as e2:
            txt = f"[page {i+1} extract error: {e2}]"
        pages_text.append(f"\n\n===== Page {i+1}/{total} =====\n{txt}")
        if (i + 1) % 20 == 0 or i + 1 == total:
            elapsed = time.time() - t0
            print(f"    [{i+1}/{total}] elapsed {elapsed:.1f}s", flush=True)

full_text = "".join(pages_text)
OUT_TXT.write_text(full_text, encoding="utf-8")
elapsed = time.time() - t0
print(f"[3] DONE in {elapsed:.1f}s", flush=True)
print(f"    Total pages: {len(pages_text)}", flush=True)
print(f"    Total chars: {len(full_text)}", flush=True)
print(f"    Saved to: {OUT_TXT}", flush=True)
print(f"    Preview (first 2000 chars):", flush=True)
print(full_text[:2000], flush=True)
