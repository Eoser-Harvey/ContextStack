const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const PORT = 8080;

const MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json",
};

const API_ROUTES = {
    "/api/price": "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD",
    "/api/histoday": "https://min-api.cryptocompare.com/data/v2/histoday?fsym=BTC&tsym=USD&limit=2000",
    "/api/fear-greed": "https://api.alternative.me/fng/",
};

function httpsGet(url) {
    return new Promise((resolve, reject) => {
        const req = https.get(url, { timeout: 20000, headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {
            let body = [];
            res.on("data", (chunk) => body.push(chunk));
            res.on("end", () => resolve({ status: res.statusCode, body: Buffer.concat(body) }));
        });
        req.on("error", reject);
        req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    });
}

function serveStatic(filePath, res) {
    const ext = path.extname(filePath);
    fs.readFile(filePath, (err, data) => {
        if (err) { res.writeHead(404); res.end("Not Found"); return; }
        res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream", "Cache-Control": "no-cache" });
        res.end(data);
    });
}

const server = http.createServer(async (req, res) => {
    res.setHeader("Access-Control-Allow-Origin", "*");
    const urlPath = req.url.split("?")[0];

    if (API_ROUTES[urlPath]) {
        try {
            const result = await httpsGet(API_ROUTES[urlPath]);
            res.writeHead(result.status, { "Content-Type": "application/json", "Cache-Control": "no-cache" });
            res.end(result.body);
        } catch (e) {
            res.writeHead(502, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: e.message }));
        }
        return;
    }

    let filePath = urlPath === "/" ? "/index.html" : urlPath;
    filePath = path.join(__dirname, filePath);

    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        serveStatic(filePath, res);
    } else {
        res.writeHead(404);
        res.end("Not Found");
    }
});

server.listen(PORT, () => {
    console.log(`Harvey Crypto 周期罗盘 - http://localhost:${PORT}`);
    for (const [r, u] of Object.entries(API_ROUTES)) console.log(`  ${r} -> ${u}`);
});
