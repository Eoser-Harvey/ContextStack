const data = {
    currentDate: new Date(),
    price: 0,
    ath: 0,
    athDate: null,
    monthsSinceAth: 0,
    tempScore: 0,
    tempLabel: "加载中",
    tempIcon: "⏳",
    decision: "正在加载市场数据...",
    ma120Price: 0,
    metrics: [
        { name: "价格跌幅（vs 本轮顶部）", value: "--", status: "normal", detail: "加载中..." },
        { name: "MVRV", value: "--", status: "normal", detail: "加载中..." },
        { name: "200日定投均价比", value: "--", status: "normal", detail: "加载中..." },
        { name: "均衡价格", value: "--", status: "normal", detail: "加载中..." },
        { name: "200周均线", value: "--", status: "normal", detail: "加载中..." },
        { name: "恐慌贪婪指数", value: "--", status: "normal", detail: "加载中..." }
    ]
};

function formatDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}年${m}月${d}日`;
}

function fmt(n) {
    if (!n || isNaN(n)) return "--";
    return Math.round(n).toLocaleString();
}

function updateTempStatus(price) {
    if (!price || price <= 0 || !data.ath || data.ath <= 0) return;
    const dropPct = ((data.ath - price) / data.ath) * 100;
    data.metrics[0].value = `-${dropPct.toFixed(1)}%`;
    data.metrics[0].detail = `当前 $${fmt(price)} · ATH $${fmt(data.ath)}（${data.athDate ? formatDate(data.athDate) : ""}）`;

    if (dropPct < 20) {
        data.tempIcon = "🔴"; data.tempLabel = "极度高估"; data.tempScore = 5.0;
        data.decision = "温度「极度高估」× 风险较高，建议观望或减仓。";
    } else if (dropPct < 35) {
        data.tempIcon = "🟠"; data.tempLabel = "高估"; data.tempScore = 4.0;
        data.decision = "温度「高估」× 可轻仓尝试，注意控制风险。";
    } else if (dropPct < 50) {
        data.tempIcon = "🟡"; data.tempLabel = "正常"; data.tempScore = 3.0;
        data.decision = "温度「正常」× 可适当配置，保持观望态度。";
    } else if (dropPct < 65) {
        data.tempIcon = "🟢"; data.tempLabel = "低估"; data.tempScore = 2.0;
        data.decision = "温度「低估」× 可逐步建仓，分批买入。";
    } else {
        data.tempIcon = "💙"; data.tempLabel = "极度低估"; data.tempScore = 1.0;
        data.decision = "温度「极度低估」× 绝佳机会，建议重仓配置！";
    }
    highlightTempBar();
}

function highlightTempBar() {
    document.querySelectorAll('.temp-label').forEach(el => el.classList.remove('current'));
    const map = { 1: 'cold', 2: 'low', 3: 'normal', 4: 'high', 5: 'extreme' };
    const cls = map[Math.round(data.tempScore)] || 'normal';
    const el = document.querySelector(`.temp-label.${cls}`);
    if (el) el.classList.add('current');
}

function calcMonthsSinceAth() {
    if (!data.athDate) return;
    const days = (Date.now() - data.athDate.getTime()) / (1000 * 60 * 60 * 24);
    data.monthsSinceAth = (days / 30).toFixed(1);
}

function render() {
    const set = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
    set("date", formatDate(data.currentDate));
    set("price", fmt(data.price));
    set("months-since-ath", data.monthsSinceAth || "--");
    set("temp-icon", data.tempIcon);
    set("temp-text", data.tempLabel);
    set("temp-score", data.tempScore ? data.tempScore.toFixed(2) : "--");
    set("temperature-label", data.tempIcon + " " + data.tempLabel);
    set("decision-text", data.decision);

    const maDiv = document.querySelector(".ma120-price");
    const maComment = document.getElementById("ma120-comment");
    if (maDiv && data.price > 0 && data.ma120Price > 0) {
        if (data.price > data.ma120Price) {
            const pct = ((data.price - data.ma120Price) / data.ma120Price * 100).toFixed(1);
            maDiv.innerHTML = `MA120 $${fmt(data.ma120Price)} · 已突破 ${pct}%`;
            if (maComment) maComment.textContent = "MA120已突破 → 小仓位右侧信号，摩擦风险高";
        } else {
            const pct = ((data.ma120Price - data.price) / data.ma120Price * 100).toFixed(1);
            maDiv.innerHTML = `MA120 $${fmt(data.ma120Price)} · 低于 ${pct}%`;
            if (maComment) maComment.textContent = "MA120未突破 → 等待更明确的信号";
        }
    }

    const grid = document.getElementById("metrics-grid");
    if (grid) {
        grid.innerHTML = data.metrics.map(m => `
            <div class="metric-card">
                <h4>${m.name}</h4>
                <div class="metric-value">${m.value}</div>
                <div class="metric-status ${m.status}">${
                    m.status === "low" ? "🟢 低估" : m.status === "high" ? "🔴 高估" : "🟡 正常"
                }</div>
                <div class="metric-detail">${m.detail}</div>
            </div>
        `).join("");
    }
}

async function apiGet(path) {
    const resp = await fetch(path);
    if (!resp.ok) throw new Error(`API ${path} 返回 ${resp.status}`);
    return resp.json();
}

async function fetchPrice() {
    try {
        const r = await apiGet("/api/price");
        if (r.USD) {
            data.price = r.USD;
            calcMonthsSinceAth();
            updateTempStatus(data.price);
            render();
        }
    } catch (e) { console.error("价格获取失败:", e); }
}

async function fetchHistoday() {
    try {
        const r = await apiGet("/api/histoday");
        if (r.Response === "Success" && r.Data && r.Data.Data) {
            const days = r.Data.Data;
            console.log(`历史数据加载: ${days.length}天, ${new Date(days[0].time*1000).toISOString()} ~ ${new Date(days[days.length-1].time*1000).toISOString()}`);

            // 1. ATH - 从全部历史中找最高价
            let maxPrice = 0, maxPriceDate = null;
            days.forEach(d => {
                if (d.high > maxPrice) {
                    maxPrice = d.high;
                    maxPriceDate = new Date(d.time * 1000);
                }
            });
            if (maxPrice > 0 && maxPriceDate) {
                data.ath = maxPrice;
                data.athDate = maxPriceDate;
                calcMonthsSinceAth();
                updateTempStatus(data.price);
                console.log(`ATH: $${fmt(maxPrice)}, 日期: ${maxPriceDate.toISOString()}`);
            }

            // 2. 200日定投均价比
            if (days.length >= 200) {
                let sum200 = 0;
                const last200 = days.slice(-200);
                last200.forEach(d => { sum200 += d.close; });
                const ma200d = sum200 / last200.length;
                const ratio200d = data.price > 0 ? (data.price / ma200d).toFixed(2) : "--";
                data.metrics[2].value = ratio200d + "x";
                data.metrics[2].detail = `200日均价 $${fmt(ma200d)}`;
                data.metrics[2].status = ratio200d < 0.8 ? "low" : ratio200d > 1.4 ? "high" : "normal";
                console.log(`200日均价: $${fmt(ma200d)}, 比值: ${ratio200d}`);
            }

            // 3. MA120
            if (days.length >= 120) {
                let sum120 = 0;
                const last120 = days.slice(-120);
                last120.forEach(d => { sum120 += d.close; });
                data.ma120Price = sum120 / last120.length;
                console.log(`MA120: $${fmt(data.ma120Price)}`);
            }

            // 4. 200周均线 (用日数据模拟：取最近1400个交易日≈200周)
            if (days.length >= 200) {
                const weekCount = 200;
                const weekDays = weekCount * 7;
                const sliceStart = Math.max(0, days.length - weekDays);
                const weekData = days.slice(sliceStart);
                // 按周聚合：每7天取最后一个close
                const weeklyCloses = [];
                for (let i = 0; i < weekData.length; i += 7) {
                    const weekSlice = weekData.slice(i, i + 7);
                    weeklyCloses.push(weekSlice[weekSlice.length - 1].close);
                }
                const last200Weeks = weeklyCloses.slice(-weekCount);
                let sum200w = 0;
                last200Weeks.forEach(c => { sum200w += c; });
                const ma200w = sum200w / last200Weeks.length;
                const ratio200w = data.price > 0 ? (data.price / ma200w).toFixed(2) : "--";
                data.metrics[4].value = ratio200w + "x";
                data.metrics[4].detail = `200WMA $${fmt(ma200w)}`;
                data.metrics[4].status = ratio200w < 0.8 ? "low" : ratio200w > 2.0 ? "high" : "normal";
                console.log(`200WMA: $${fmt(ma200w)}, 比值: ${ratio200w}, 周数: ${last200Weeks.length}`);
            }

            // 5. 均衡价格（实现价格 = 历史均价的50%分位）
            let sumAll = 0;
            days.forEach(d => { sumAll += d.close; });
            const avgPrice = sumAll / days.length;
            const eqPrice = avgPrice * 0.45;
            data.metrics[3].value = `$${fmt(eqPrice)}`;
            data.metrics[3].detail = `均衡价 $${fmt(eqPrice)}（历史均价$${fmt(avgPrice)}×0.45）`;
            data.metrics[3].status = data.price < eqPrice ? "low" : data.price > avgPrice ? "high" : "normal";
            console.log(`均衡价格: $${fmt(eqPrice)}, 历史均价: $${fmt(avgPrice)}`);

            // 6. MVRV 估算（用价格/实现价格比率，实现价格≈历史均价）
            if (data.price > 0 && avgPrice > 0) {
                const mvrv = (data.price / avgPrice).toFixed(2);
                data.metrics[1].value = mvrv;
                data.metrics[1].detail = `MVRV=${mvrv}（价格/历史均价$${fmt(avgPrice)}）`;
                data.metrics[1].status = mvrv < 1.0 ? "low" : mvrv > 3.5 ? "high" : "normal";
                console.log(`MVRV: ${mvrv}`);
            }
        }
    } catch (e) { console.error("历史数据获取失败:", e); }
}

async function fetchFearGreed() {
    try {
        const r = await apiGet("/api/fear-greed");
        if (r.data && r.data.length > 0) {
            const v = parseInt(r.data[0].value);
            data.metrics[5].value = v;
            data.metrics[5].detail = r.data[0].value_classification;
            data.metrics[5].status = v < 25 ? "low" : v > 75 ? "high" : "normal";
            console.log(`恐慌贪婪: ${v} (${r.data[0].value_classification})`);
        }
    } catch (e) { console.error("恐慌贪婪指数获取失败:", e); }
}

async function fetchAll() {
    await fetchPrice();
    await Promise.all([fetchHistoday(), fetchFearGreed()]);
    render();
}

render();
fetchAll();

setInterval(() => {
    data.currentDate = new Date();
    fetchPrice();
}, 30000);
