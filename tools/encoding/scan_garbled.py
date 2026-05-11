import os
import re

def is_garbled(text):
    """Check if text contains garbled characters (private use area, etc.)"""
    garbled_count = 0
    total_cjk = 0
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF:
            total_cjk += 1
        elif 0xE000 <= cp <= 0xF8FF:
            garbled_count += 1
        elif 0xF900 <= cp <= 0xFAFF:
            garbled_count += 1
    if total_cjk > 0 and garbled_count > 0:
        return True, garbled_count, total_cjk
    return False, 0, 0

def scan_directory(root):
    garbled_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ['.git', '__pycache__', '.trae', 'backup_archive']]
        for fname in filenames:
            if not fname.endswith(('.md', '.txt', '.bat', '.ps1', '.json')):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                is_g, gc, tc = is_garbled(content)
                if is_g:
                    rel = os.path.relpath(fpath, root)
                    garbled_files.append((rel, gc, tc))
            except Exception as e:
                print(f"Error reading {fpath}: {e}")
    return garbled_files

root = r'd:\MyFile\AI\ContextStack'
results = scan_directory(root)

if results:
    print(f"Found {len(results)} files with garbled characters:")
    for rel, gc, tc in sorted(results):
        print(f"  {rel} (garbled: {gc}, total CJK: {tc})")
else:
    print("No garbled files found!")
