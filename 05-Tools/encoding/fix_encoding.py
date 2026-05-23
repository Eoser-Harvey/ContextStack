import os
import re

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')

SKIP_DIRS = {'backup_archive', 'backup_before_restore', '.git', '__pycache__', 'node_modules', 'history'}
SKIP_SUFFIXES = {'.png', '.jpg', '.json', '.code-workspace', '.bat', '.ps1', '.exe', '.dll', '.py', '.pyc'}

def is_garbled_char(ch):
    """Check if a character looks like mojibake (UTF-8 bytes decoded as Latin-1)"""
    cp = ord(ch)
    if cp < 0x80:
        return False
    if 0x4E00 <= cp <= 0x9FFF:
        return False
    if 0x3400 <= cp <= 0x4DBF:
        return False
    if 0x20000 <= cp <= 0x2A6DF:
        return False
    if 0xF900 <= cp <= 0xFAFF:
        return False
    if 0x3000 <= cp <= 0x303F:
        return False
    if 0xFF00 <= cp <= 0xFFEF:
        return False
    if 0x0020 <= cp <= 0x007E:
        return False
    return True

def count_garbled(text):
    """Count characters that look like mojibake"""
    count = 0
    for ch in text:
        if is_garbled_char(ch):
            count += 1
    return count

def try_fix(text):
    """Try to fix mojibake by reversing Latin-1 → UTF-8 corruption"""
    try:
        fixed = text.encode('latin-1').decode('utf-8')
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None

def try_fix_cp1252(text):
    """Try to fix mojibake by reversing CP1252 → UTF-8 corruption"""
    try:
        fixed = text.encode('cp1252').decode('utf-8')
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f'  SKIP (read error): {e}')
        return False

    if not content.strip():
        return False

    garbled_before = count_garbled(content)
    if garbled_before == 0:
        return False

    fixed = try_fix(content)
    if fixed is None:
        fixed = try_fix_cp1252(content)

    if fixed is None:
        print(f'  FAIL: cannot fix encoding')
        return False

    garbled_after = count_garbled(fixed)
    if garbled_after >= garbled_before:
        print(f'  SKIP: fix made it worse or same ({garbled_before} -> {garbled_after})')
        return False

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed)

    print(f'  FIXED: {garbled_before} garbled chars -> {garbled_after}')
    return True

def main():
    fixed_count = 0
    skip_count = 0

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SKIP_SUFFIXES:
                continue
            if filename.endswith('.backup') or filename.endswith('.backup_enc') or \
               filename.endswith('.backup_context') or filename.endswith('.backup_final2') or \
               filename.endswith('.backup_pre_fix') or filename.endswith('.backup_ftfy') or \
               filename.endswith('.before_restore') or filename.endswith('.backup_final') or \
               filename.endswith('.backup_lang') or filename.endswith('.backup_before_fix'):
                continue

            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, ROOT)

            if fix_file(filepath):
                fixed_count += 1
            else:
                skip_count += 1

    print(f'\nDone. Fixed: {fixed_count}, Skipped: {skip_count}')

if __name__ == '__main__':
    main()
