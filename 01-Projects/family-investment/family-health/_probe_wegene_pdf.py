"""
Probe WeGene PDF: check page count and whether pages have text or are image-based.
"""
import time
from pathlib import Path

PDF_PATH = r"E:\Personal Files\0.家庭健康\微基金检查报告-燕.pdf"
print(f"File: {PDF_PATH}", flush=True)
print(f"Size: {Path(PDF_PATH).stat().st_size / 1024 / 1024:.1f} MB", flush=True)

t0 = time.time()
try:
    import pypdf
    print("[1] Opening with pypdf...", flush=True)
    reader = pypdf.PdfReader(PDF_PATH)
    total = len(reader.pages)
    print(f"    Total pages: {total}", flush=True)
    print(f"    Open time: {time.time()-t0:.1f}s", flush=True)

    # Sample first 5 pages
    print("\n[2] Sampling first 5 pages:", flush=True)
    for i in range(min(5, total)):
        pt0 = time.time()
        try:
            page = reader.pages[i]
            txt = page.extract_text() or ""
            # Check images on page
            images = []
            try:
                images = list(page.images)
            except Exception:
                pass
            print(f"  Page {i+1}: text_len={len(txt)}, images={len(images)}, time={time.time()-pt0:.2f}s", flush=True)
            if txt.strip():
                print(f"    Preview: {txt[:300]!r}", flush=True)
        except Exception as e:
            print(f"  Page {i+1} ERROR: {e}", flush=True)

    # Sample middle and last
    print("\n[3] Sampling middle and last pages:", flush=True)
    sample_indices = [total // 2, total - 1] if total > 5 else []
    for i in sample_indices:
        pt0 = time.time()
        try:
            page = reader.pages[i]
            txt = page.extract_text() or ""
            images = []
            try:
                images = list(page.images)
            except Exception:
                pass
            print(f"  Page {i+1}: text_len={len(txt)}, images={len(images)}, time={time.time()-pt0:.2f}s", flush=True)
            if txt.strip():
                print(f"    Preview: {txt[:300]!r}", flush=True)
        except Exception as e:
            print(f"  Page {i+1} ERROR: {e}", flush=True)

except Exception as e:
    print(f"[!] pypdf failed: {e}", flush=True)

print(f"\nTotal probe time: {time.time()-t0:.1f}s", flush=True)
