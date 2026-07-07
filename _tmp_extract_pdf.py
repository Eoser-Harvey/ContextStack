import os, glob, json

SRC = r"D:\wechatDownload\下载\老薛的晨间日记"
OUT = r"e:\ProjectGroup\AI\ContextStack\_tmp_laoxue"
os.makedirs(OUT, exist_ok=True)

import pdfplumber

def sp(s):
    # safe print to gbk console
    try:
        print(s)
    except Exception:
        print(s.encode("gbk", "replace").decode("gbk"))

pdfs = sorted(glob.glob(os.path.join(SRC, "*.pdf")))
total = len(pdfs)
sp(f"Found {total} PDFs")

manifest = []
ok = 0
for i, p in enumerate(pdfs):
    base = os.path.splitext(os.path.basename(p))[0]
    out_path = os.path.join(OUT, base + ".txt")
    try:
        with pdfplumber.open(p) as pdf:
            pages = [ (pg.extract_text() or "") for pg in pdf.pages ]
        text = "\n\n".join(pages)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        ok += 1
        first = text.strip().replace("\n", " ")[:50]
        manifest.append({"file": base, "pages": len(pages), "chars": len(text)})
        sp(f"[{i+1}/{total}] OK ({len(pages)}p,{len(text)}c) {base}")
    except Exception as e:
        sp(f"[{i+1}/{total}] FAIL {base} :: {e}")

with open(os.path.join(OUT, "_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
sp(f"\nDONE. {ok}/{total} extracted")
