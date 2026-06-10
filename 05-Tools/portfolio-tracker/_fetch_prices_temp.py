"""临时价格拉取脚本 — 测试多个备用数据源"""
import requests, json

# 1. 汇率 (exchangerate-api 已验证可用)
try:
    r = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=15)
    data = r.json()
    usd_cny = data['rates']['CNY']
    usd_hkd = data['rates']['HKD']
    hkd_cny = usd_cny / usd_hkd
    print(f"汇率: USD/CNY={usd_cny:.4f}, HKD/CNY={hkd_cny:.4f}")
except Exception as e:
    print(f"汇率失败: {e}")
    usd_cny, hkd_cny = 7.25, 0.93

# 2. BTC/ETH — 试多个来源
btc_price = eth_price = None
sources = [
    ("OKX", "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"),
    ("Gate", "https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT"),
    ("MEXC", "https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT"),
    ("Bybit", "https://api.bybit.com/v5/market/tickers?category=spot&symbol=BTCUSDT"),
    ("KuCoin", "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT"),
]

for name, url in sources:
    try:
        r = requests.get(url, timeout=10)
        if r.ok:
            print(f"  {name} OK: {r.status_code}")
            # Parse differently per exchange
            data = r.json()
            if name == "OKX":
                btc_price = float(data['data'][0]['last'])
                # Get ETH too
                r2 = requests.get("https://www.okx.com/api/v5/market/ticker?instId=ETH-USDT", timeout=10)
                if r2.ok:
                    eth_price = float(r2.json()['data'][0]['last'])
            elif name == "Gate":
                btc_price = float(data[0]['last'])
                r2 = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=ETH_USDT", timeout=10)
                if r2.ok:
                    eth_price = float(r2.json()[0]['last'])
            elif name == "MEXC":
                btc_price = float(data['price'])
                r2 = requests.get("https://api.mexc.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=10)
                if r2.ok:
                    eth_price = float(r2.json()['price'])
            elif name == "Bybit":
                btc_price = float(data['result']['list'][0]['lastPrice'])
                r2 = requests.get("https://api.bybit.com/v5/market/tickers?category=spot&symbol=ETHUSDT", timeout=10)
                if r2.ok:
                    eth_price = float(r2.json()['result']['list'][0]['lastPrice'])
            elif name == "KuCoin":
                btc_price = float(data['data']['price'])
                r2 = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=ETH-USDT", timeout=10)
                if r2.ok:
                    eth_price = float(r2.json()['data']['price'])
            if btc_price:
                break
    except Exception as e:
        print(f"  {name} fail: {type(e).__name__}")

print(f"BTC: {btc_price}, ETH: {eth_price}")

# 3. 股票 — 试新浪财经 API (国内可访问)
# 港股 1810.HK → 小米
try:
    r = requests.get("https://hq.sinajs.cn/list=hk01810", timeout=15,
                     headers={"Referer": "https://finance.sina.com.cn"})
    r.encoding = "gbk"
    text = r.text
    if '"' in text:
        parts = text.split('"')[1].split(',')
        # hk stock format: name,open,prev_close,high,low,price,...
        if len(parts) > 6:
            print(f"小米: HK${parts[6]}")
except Exception as e:
    print(f"小米 fail: {e}")

# MRVL — 美股需要特殊处理，试 sina us stock
try:
    r = requests.get("https://hq.sinajs.cn/list=gb_mrvl", timeout=15,
                     headers={"Referer": "https://finance.sina.com.cn"})
    r.encoding = "gbk"
    text = r.text
    if '"' in text:
        parts = text.split('"')[1].split(',')
        if len(parts) > 1:
            print(f"MRVL: ${parts[1]}")
except Exception as e:
    print(f"MRVL sina fail: {e}")