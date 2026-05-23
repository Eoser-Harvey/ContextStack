import os

def analyze_file(path):
    with open(path, 'rb') as f:
        data = f.read()
    print(f'File: {os.path.basename(path)}')
    print(f'Size: {len(data)} bytes')
    print(f'First 300 bytes hex:')
    print(' '.join(f'{b:02x}' for b in data[:300]))
    print()
    print('As UTF-8:')
    try:
        print(data[:300].decode('utf-8'))
    except:
        print('(decode failed)')
    print()
    print('As GBK:')
    try:
        print(data[:300].decode('gbk'))
    except:
        print('(decode failed)')

analyze_file(os.path.join(os.path.dirname(__file__), '..', '..', '02-Knowledge', 'system', 'index.md'))
print('\n' + '='*60 + '\n')
analyze_file(os.path.join(os.path.dirname(__file__), '..', '..', 'FRAMEWORK-README.md'))
