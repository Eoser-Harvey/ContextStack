with open(r'd:\MyFile\AI\ContextStack\ContextStack协作架构.md', 'rb') as f:
    data = f.read()

idx = data.find('架构'.encode('utf-8'))
if idx >= 0:
    print(f'Found 架构 at offset {idx}')
    chunk = data[idx:idx+30]
    print(f'Bytes: {chunk.hex()}')
    print(f'As UTF-8: {chunk.decode("utf-8", errors="replace")}')
else:
    print('架构 not found')
    idx = data.find('鏋舵瀯'.encode('utf-8'))
    if idx >= 0:
        print(f'Found 鏋舵瀯 at offset {idx}')
        chunk = data[idx:idx+30]
        print(f'Bytes: {chunk.hex()}')
        print(f'As UTF-8: {chunk.decode("utf-8", errors="replace")}')
    else:
        print('Neither found, first 100 bytes:')
        print(data[:100].hex())
        print(data[:100].decode('utf-8', errors='replace'))
