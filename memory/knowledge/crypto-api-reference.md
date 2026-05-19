# Crypto 数据 API 知识库

> 本文档汇总加密货币相关公开免费API，方便后续项目复用

## 国内可用性测试（2026-05-19）

| API | 国内直连 | 备注 |
|---|---|---|
| CryptoCompare | ✅ 可用 | 推荐，免费额度充足 |
| Alternative.me | ✅ 可用 | 恐慌贪婪指数，无限制 |
| Binance | ❌ 被墙 | ECONNRESET，需代理 |
| CoinGecko | ❌ 被墙 | ECONNRESET，需代理 |
| CoinCap | ❓ 未测试 | - |
| Blockchain.com | ❓ 未测试 | - |

---

## 1. CryptoCompare API（推荐）

**官网**: https://min-api.cryptocompare.com/
**免费额度**: 每月100,000次调用（无Key），注册免费Key后30万次/月
**国内可用**: ✅ 直连无问题
**速率限制**: 无Key约30次/秒，有Key更高

### 1.1 实时价格

```
GET https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD
```

**响应示例**:
```json
{"USD": 76818.08}
```

**参数**:
- `fsym`: 源币种（BTC, ETH, SOL等）
- `tsyms`: 目标货币（USD, CNY等，逗号分隔多个）
- `api_key`: 可选，提升速率限制

**多币种多法币**:
```
GET /data/price?fsym=BTC&tsyms=USD,CNY,EUR
→ {"USD": 76818, "CNY": 556000, "EUR": 71000}
```

### 1.2 历史日线数据

```
GET https://min-api.cryptocompare.com/data/v2/histoday?fsym=BTC&tsym=USD&limit=2000
```

**响应示例**:
```json
{
  "Response": "Success",
  "Data": {
    "Data": [
      {"time": 1606348800, "high": 19486, "low": 18850, "open": 19150, "close": 19050, "volumefrom": 1234, "volumeto": 23456789}
    ]
  }
}
```

**参数**:
- `fsym`: 源币种
- `tsym`: 目标货币
- `limit`: 返回天数（最大2000，约5.5年）
- `toTs`: 可选，结束时间戳（默认当前）
- `aggregate`: 可选，聚合天数（如7=周线，但实测不稳定，建议自行聚合）

**注意**:
- `limit=2000` 返回约2001条数据（从2020-11至今）
- `aggregate=7` 参数在某些情况下返回0条数据，**建议前端自行按7天聚合**
- `time` 字段为Unix时间戳（秒）

### 1.3 多币种价格

```
GET https://min-api.cryptocompare.com/data/pricemulti?fsyms=BTC,ETH,SOL&tsyms=USD
```

**响应示例**:
```json
{"BTC": {"USD": 76818}, "ETH": {"USD": 2850}, "SOL": {"USD": 165}}
```

### 1.4 历史小时线

```
GET https://min-api.cryptocompare.com/data/v2/histohour?fsym=BTC&tsym=USD&limit=720
```

**参数**: 同 histoday，limit最大2000

### 1.5 历史分钟线

```
GET https://min-api.cryptocompare.com/data/v2/histominute?fsym=BTC&tsym=USD&limit=1440
```

**参数**: limit最大2000

---

## 2. Alternative.me API（恐慌贪婪指数）

**官网**: https://alternative.me/crypto/fear-and-greed-index/
**免费额度**: 无限制
**国内可用**: ✅ 直连无问题
**更新频率**: 每天一次

### 2.1 最新恐慌贪婪指数

```
GET https://api.alternative.me/fng/
```

**响应示例**:
```json
{
  "name": "Fear and Greed Index",
  "data": [
    {
      "value": "25",
      "value_classification": "Extreme Fear",
      "timestamp": "1779148800",
      "time_until_update": "43834"
    }
  ]
}
```

**字段说明**:
- `value`: 0-100，0=极度恐慌，100=极度贪婪
- `value_classification`: Extreme Fear / Fear / Neutral / Greed / Extreme Greed
- `timestamp`: Unix时间戳
- `time_until_update`: 距下次更新的秒数

### 2.2 历史数据

```
GET https://api.alternative.me/fng/?limit=30&format=json
```

**参数**:
- `limit`: 返回天数（默认10，最大不限）
- `format`: json 或 csv
- `date_format`: us/cn/kr/world（日期格式）

---

## 3. Binance API（国内需代理）

**官网**: https://binance-docs.github.io/apidocs/
**免费额度**: 无限制（有速率限制1200次/分钟）
**国内可用**: ❌ 被墙，需VPN或代理

### 3.1 实时价格

```
GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
```

**响应**: `{"symbol":"BTCUSDT","price":"76818.08000000"}`

### 3.2 K线数据

```
GET https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1w&limit=200
```

**interval**: 1m/5m/15m/1h/4h/1d/1w/1M
**limit**: 最大1000

---

## 4. CoinGecko API（国内需代理）

**官网**: https://www.coingecko.com/en/api
**免费额度**: 30次/分钟（Demo Key）
**国内可用**: ❌ 被墙，需VPN或代理

### 4.1 币种详情

```
GET https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&community_data=false&developer_data=false
```

### 4.2 简单价格

```
GET https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
```

---

## 5. 实战经验与踩坑记录

### 5.1 CORS 问题
- 浏览器直接请求外部API会被CORS拦截
- **解决方案**: Node.js后端代理（server.js），前端请求本地 `/api/xxx`，后端转发到外部API

### 5.2 国内网络问题
- Binance/CoinGecko 在国内直连返回 ECONNRESET
- **解决方案**: 使用 CryptoCompare 替代（国内可直连）

### 5.3 CryptoCompare aggregate 参数不可靠
- `histoday?aggregate=7` 有时返回0条数据
- **解决方案**: 取日数据后前端自行按7天聚合计算周线

### 5.4 数据量与计算
- `limit=2000` 约返回5.5年日线数据（足够计算ATH、MA120、200WMA等）
- 2000天数据JSON约36KB，加载时间约2-5秒
- 所有指标（ATH、MA、MVRV、均衡价格）可从单一histoday数据源计算

### 5.5 浏览器缓存问题
- 更新JS后浏览器可能使用缓存版本
- **解决方案**: 引用加版本号 `app.js?v=4`，或设置 `Cache-Control: no-cache`

### 5.6 并行请求渲染冲突
- 多个API并行请求时，各自调用render()会导致后到的数据被覆盖
- **解决方案**: 所有API请求完成后统一调用一次render()

---

## 6. 常用指标计算方法

### 6.1 ATH（历史最高价）
从histoday全部数据中找 `high` 最大值

### 6.2 MA120（120日均线）
最近120天 `close` 的算术平均值

### 6.3 200日定投均价比
当前价格 / 最近200天close平均值

### 6.4 200周均线（200WMA）
日数据按7天聚合成周线，取最近200周close平均值

### 6.5 MVRV估算
当前价格 / 历史均价（简化估算，真实MVRV需要链上实现价格数据）

### 6.6 均衡价格
历史均价 × 0.45（经验系数，约等于实现价格的50%分位）

### 6.7 综合市场温度
基于当前价格 vs ATH 跌幅百分比：
| 跌幅 | 温度 | 评分 |
|---|---|---|
| < 20% | 极度高估 | 5.0 |
| 20-35% | 高估 | 4.0 |
| 35-50% | 正常 | 3.0 |
| 50-65% | 低估 | 2.0 |
| > 65% | 极度低估 | 1.0 |

---

## 7. Node.js 代理模板

```javascript
// 最小化代理服务器模板
const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const API_ROUTES = {
    "/api/price": "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD",
    "/api/histoday": "https://min-api.cryptocompare.com/data/v2/histoday?fsym=BTC&tsym=USD&limit=2000",
    "/api/fear-greed": "https://api.alternative.me/fng/",
};

http.createServer(async (req, res) => {
    res.setHeader("Access-Control-Allow-Origin", "*");
    const urlPath = req.url.split("?")[0];

    if (API_ROUTES[urlPath]) {
        try {
            const result = await new Promise((resolve, reject) => {
                https.get(API_ROUTES[urlPath], { timeout: 15000, headers: { "User-Agent": "Mozilla/5.0" } }, (r) => {
                    let body = [];
                    r.on("data", (c) => body.push(c));
                    r.on("end", () => resolve({ status: r.statusCode, body: Buffer.concat(body) }));
                }).on("error", reject);
            });
            res.writeHead(result.status, { "Content-Type": "application/json" });
            res.end(result.body);
        } catch (e) {
            res.writeHead(502, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: e.message }));
        }
        return;
    }

    // 静态文件服务
    let filePath = urlPath === "/" ? "/index.html" : urlPath;
    filePath = path.join(__dirname, filePath);
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        fs.readFile(filePath, (err, data) => {
            if (err) { res.writeHead(404); res.end("Not Found"); return; }
            const ext = path.extname(filePath);
            const mime = { ".html": "text/html", ".css": "text/css", ".js": "application/javascript" };
            res.writeHead(200, { "Content-Type": (mime[ext] || "application/octet-stream") + "; charset=utf-8" });
            res.end(data);
        });
    }
}).listen(8080);
```

---

**创建时间**: 2026-05-19
**适用项目**: btc-temperature-gauge 及后续Crypto相关项目
**维护原则**: 发现新可用API或踩坑时及时更新
