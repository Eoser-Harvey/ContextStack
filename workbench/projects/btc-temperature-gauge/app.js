const data = {
    currentDate: new Date(),
    price: 79564,
    ath: 126200,
    monthsSinceAth: 7.2,
    tempScore: 3.0,
    tempLabel: "正常",
    tempIcon: "🟡",
    decision: "温度「正常」× MA120已突破，小仓位右侧信号。左侧指标未触底，被摩擦风险高，轻仓或观望均可。",
    ma120Price: 74569,
    ma120BreakoutPercent: 6.3,
    metrics: [
        {
            name: "价格跌幅（vs 本轮顶部）",
            value: "-37.0%",
            status: "normal",
            detail: "$79,564 · ATH $126,200"
        },
        {
            name: "MVRV",
            value: "1.48",
            status: "normal",
            detail: "历史百分位 P36"
        },
        {
            name: "200日定投均价比",
            value: "0.97x",
            status: "normal",
            detail: "均价 $82,190"
        },
        {
            name: "均衡价格",
            value: "$40,424",
            status: "normal",
            detail: "当前高于均衡价 $40,424"
        },
        {
            name: "200周均线",
            value: "1.30x",
            status: "normal",
            detail: "200WMA $61,103"
        },
        {
            name: "恐慌贪婪指数",
            value: "46",
            status: "normal",
            detail: "历史百分位 P57"
        }
    ]
};

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}年${month}月${day}日`;
}

function formatNumber(num) {
    return num.toLocaleString();
}

function updateTempStatus(price) {
    const dropPercent = ((data.ath - price) / data.ath) * 100;
    data.metrics[0].value = `-${dropPercent.toFixed(1)}%`;
    data.metrics[0].detail = `$${formatNumber(Math.round(price))} · ATH $${formatNumber(data.ath)}`;

    if (dropPercent < 20) {
        data.tempIcon = "🔴";
        data.tempLabel = "极度高估";
        data.tempScore = 5.0;
    } else if (dropPercent < 35) {
        data.tempIcon = "🟠";
        data.tempLabel = "高估";
        data.tempScore = 4.0;
    } else if (dropPercent < 50) {
        data.tempIcon = "🟡";
        data.tempLabel = "正常";
        data.tempScore = 3.0;
    } else if (dropPercent < 65) {
        data.tempIcon = "🟢";
        data.tempLabel = "低估";
        data.tempScore = 2.0;
    } else {
        data.tempIcon = "💙";
        data.tempLabel = "极度低估";
        data.tempScore = 1.0;
    }
}

function render() {
    document.getElementById("date").textContent = formatDate(data.currentDate);
    document.getElementById("price").textContent = formatNumber(Math.round(data.price));
    document.getElementById("months-since-ath").textContent = data.monthsSinceAth;
    document.getElementById("temp-icon").textContent = data.tempIcon;
    document.getElementById("temp-text").textContent = data.tempLabel;
    document.getElementById("temp-score").textContent = data.tempScore.toFixed(2);
    document.getElementById("temperature-label").textContent = data.tempIcon + " " + data.tempLabel;
    document.getElementById("decision-text").textContent = data.decision;
    document.getElementById("ma120-price").textContent = formatNumber(data.ma120Price);
    document.getElementById("ma120-comment").textContent = "MA120已突破 → 小仓位右侧信号，摩擦风险高";

    const metricsGrid = document.getElementById("metrics-grid");
    metricsGrid.innerHTML = data.metrics.map(metric => `
        <div class="metric-card">
            <h4>${metric.name}</h4>
            <div class="metric-value">${metric.value}</div>
            <div class="metric-status ${metric.status}">${metric.status === "normal" ? "🟡 正常" : metric.status === "low" ? "🟢 低估" : "🔴 高估"}</div>
            <div class="metric-detail">${metric.detail}</div>
        </div>
    `).join("");
}

async function fetchRealTimePrice() {
    try {
        const response = await fetch("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT");
        const result = await response.json();
        if (result.price) {
            data.price = parseFloat(result.price);
            updateTempStatus(data.price);
            render();
        }
    } catch (error) {
        console.error("获取实时价格失败:", error);
    }
}

render();
fetchRealTimePrice();

setInterval(() => {
    fetchRealTimePrice();
    data.currentDate = new Date();
}, 30000);
