"""
Extract key chapters from WeGene PDF (3607 pages).
Strategy:
1. Open once (98s)
2. Locate chapter page ranges from TOC pages 2-10
3. Extract only: 健康风险 / 营养代谢 / 药物代谢 / 运动基因 / 祖源 / 父系母系
"""
import time
import re
from pathlib import Path

PDF_PATH = r"E:\Personal Files\0.家庭健康\微基金检查报告-燕.pdf"
OUT_DIR = Path(r"e:\ProjectGroup\AI\ContextStack\01-Projects\family-hub\family-health")
OUT_TXT = OUT_DIR / "_wegene_pdf_key.txt"

print(f"[1] Opening PDF (98s expected)...", flush=True)
t0 = time.time()
import pypdf
reader = pypdf.PdfReader(PDF_PATH)
total = len(reader.pages)
print(f"    Total pages: {total}, open time: {time.time()-t0:.1f}s", flush=True)

# Step 2: Extract all TOC pages (first 15) to find chapter boundaries
print("\n[2] Extracting TOC pages (1-15)...", flush=True)
toc_text = ""
for i in range(min(15, total)):
    txt = reader.pages[i].extract_text() or ""
    toc_text += f"\n=== TOC Page {i+1} ===\n{txt}"
print(toc_text[:3000], flush=True)

# Step 3: Identify key chapter page ranges by scanning page texts
# From TOC sample we saw: 健康风险 around page 131+, 营养代谢 around 61+, 药物代谢 likely later
# We will scan all pages but only extract text for pages matching key keywords
print("\n[3] Scanning all pages for key chapters...", flush=True)

KEY_PATTERNS = [
    # (chapter_name, regex_to_identify_page_in_chapter)
    ("祖源分析", r"祖源|单倍群|尼安德特"),
    ("运动基因", r"咖啡因敏感|碳⽔化合物敏感|耐⼒|爆发⼒|摄氧量|跟腱|韧带|腰椎间盘"),
    ("营养代谢", r"乳糖代谢|咖啡因代谢|叶酸|钙营养|酒精代谢|维⽣素|铁营养|锌营养|镁营养"),
    ("健康风险", r"癌|⻛险|⼼⽅|⼼⾎管|糖尿病|⾼⾎压|⾎栓|甲状腺|乳腺|⾃⾝免疫|帕⾦森|阿尔茨海默|肥胖"),
    ("药物代谢", r"药物代谢|氯吡格雷|华法林|CYP|代谢能⼒|用药"),
    ("特质基因", r"特质|⽓味|苦味|⽑发|⽪肤|近视|睡眠"),
]

# Compile a single regex for fast match
import re
combined_re = re.compile("|".join(p for _, p in KEY_PATTERNS))

key_pages = []  # list of (page_num, chapter, text)
chapter_counts = {name: 0 for name, _ in KEY_PATTERNS}

t_scan = time.time()
for i in range(total):
    try:
        txt = reader.pages[i].extract_text() or ""
    except Exception:
        continue
    if not txt.strip():
        continue
    # Detect chapter for this page
    detected_chapters = []
    for name, pat in KEY_PATTERNS:
        if re.search(pat, txt):
            detected_chapters.append(name)
            chapter_counts[name] += 1
    if detected_chapters:
        key_pages.append((i + 1, "/".join(detected_chapters), txt))
    if (i + 1) % 500 == 0:
        print(f"    scanned {i+1}/{total}, key_pages so far: {len(key_pages)}, elapsed: {time.time()-t_scan:.1f}s", flush=True)

print(f"\n[4] Scan done in {time.time()-t_scan:.1f}s", flush=True)
print(f"    Chapter page counts: {chapter_counts}", flush=True)
print(f"    Total key pages: {len(key_pages)}", flush=True)

# Step 4: Save all key pages text
print("\n[5] Writing key pages to file...", flush=True)
with open(OUT_TXT, "w", encoding="utf-8") as f:
    f.write(f"# WeGene 关键章节提取 (共 {len(key_pages)}/{total} 页)\n")
    f.write(f"# 章节统计: {chapter_counts}\n\n")
    for page_num, chapter, txt in key_pages:
        f.write(f"\n\n===== Page {page_num} [{chapter}] =====\n{txt}\n")

size_mb = OUT_TXT.stat().st_size / 1024 / 1024
print(f"    Saved: {OUT_TXT} ({size_mb:.1f} MB)", flush=True)

# Step 6: Extract specific high-value findings
print("\n[6] Searching for specific high-value keywords...", flush=True)

SEARCH_TERMS = [
    "叶酸", "MTHFR", "甲状腺", "乳腺", "BRCA",
    "糖尿病", "FTO", "⾎栓", "易栓", "Factor V", "F5",
    "CYP2C19", "CYP2D6", "CYP4F2", "氯吡格雷",
    "APOE", "阿尔茨海默", "APOC1",
    "ALDH2", "ADH1B", "酒精",
    "LCT", "乳糖", "MCM6",
    "9p21", "rs1333049", "冠⼼病", "冠心",
    "⾼⾎压", "AGT", "AGTR1",
    "肺癌", "CHRNA3", "TERT",
    "结直肠癌", "8q24", "rs6983267",
    "帕⾦森", "SNCA",
    "祖源", "单倍群",
]

findings = {term: [] for term in SEARCH_TERMS}
for page_num, chapter, txt in key_pages:
    for term in SEARCH_TERMS:
        if term in txt:
            # Find surrounding context (200 chars before/after)
            idx = 0
            while True:
                idx = txt.find(term, idx)
                if idx == -1:
                    break
                start = max(0, idx - 100)
                end = min(len(txt), idx + 300)
                ctx = txt[start:end].replace("\n", " ")
                findings[term].append((page_num, ctx))
                idx += 1

# Save findings
OUT_FIND = OUT_DIR / "_wegene_findings.txt"
with open(OUT_FIND, "w", encoding="utf-8") as f:
    for term, hits in findings.items():
        f.write(f"\n\n{'='*60}\n## {term} ({len(hits)} hits)\n{'='*60}\n")
        # Limit to first 5 hits per term to keep file manageable
        for page_num, ctx in hits[:5]:
            f.write(f"\n[Page {page_num}] ...{ctx}...\n")

size_find = OUT_FIND.stat().st_size / 1024
print(f"    Findings saved: {OUT_FIND} ({size_find:.1f} KB)", flush=True)

print(f"\n[7] Summary of findings count:", flush=True)
for term, hits in findings.items():
    print(f"    {term}: {len(hits)} hits", flush=True)

print(f"\n[DONE] Total time: {time.time()-t0:.1f}s", flush=True)
