import os

def try_fix_gbk_to_utf8(text):
    """Try: garbled text -> latin-1 bytes -> decode as GBK"""
    try:
        raw = text.encode('latin-1')
        fixed = raw.decode('gbk')
        return fixed
    except:
        return None

def try_fix_utf8_to_gbk(text):
    """Try: garbled text -> latin-1 bytes -> decode as UTF-8"""
    try:
        raw = text.encode('latin-1')
        fixed = raw.decode('utf-8')
        return fixed
    except:
        return None

def try_fix_gbk_misread(text):
    """Try: text was GBK, read as latin-1, encoded as UTF-8"""
    try:
        raw = text.encode('latin-1')
        fixed = raw.decode('gbk')
        return fixed
    except:
        return None

# Test with a known garbled string
test = "璁捐"
print(f"Original garbled: {test}")
print(f"  hex: {test.encode('utf-8').hex()}")

# Try different fixes
fixed1 = try_fix_gbk_to_utf8(test)
print(f"Fix1 (latin1->gbk): {fixed1}")

fixed2 = try_fix_utf8_to_gbk(test)
print(f"Fix2 (latin1->utf8): {fixed2}")

# Try with a longer sample
sample = "架构璁捐"
print(f"\nLonger sample: {sample}")
fixed = try_fix_gbk_to_utf8(sample)
print(f"Fix1: {fixed}")

# Try the reverse: what if we take the expected text and see how it becomes garbled
expected = "设计"
print(f"\nExpected: {expected}")
print(f"  UTF-8 hex: {expected.encode('utf-8').hex()}")
print(f"  GBK hex: {expected.encode('gbk').hex()}")

# What if we take GBK bytes and decode as UTF-8?
try:
    gbk_bytes = expected.encode('gbk')
    as_utf8 = gbk_bytes.decode('utf-8')
    print(f"  GBK->UTF-8 misread: {as_utf8}")
    print(f"  hex: {as_utf8.encode('utf-8').hex()}")
except:
    print("  GBK->UTF-8 failed")

# What if we take UTF-8 bytes and decode as GBK?
try:
    utf8_bytes = expected.encode('utf-8')
    as_gbk = utf8_bytes.decode('gbk')
    print(f"  UTF-8->GBK misread: {as_gbk}")
    print(f"  hex: {as_gbk.encode('utf-8').hex()}")
except:
    print("  UTF-8->GBK failed")
