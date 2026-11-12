"""
A股行情看盘 - FastAPI 后端
数据源: akshare (pip install akshare)
接口文档: http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import akshare as ak
import pandas as pd
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kaipan")

app = FastAPI(title="A股行情API", version="1.0.0", description="同花顺看盘后端，封装 akshare")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def clean(code: str) -> str:
    """清理股票代码: 600036.SH → 600036, sh000001 → 000001"""
    s = str(code).strip()
    s = re.sub(r"\.(SH|SZ|BJ|SS)$", "", s, flags=re.I)
    s = re.sub(r"^(SH|SZ|BJ)", "", s, flags=re.I)
    stripped = s.lstrip("0")
    return stripped.zfill(6) if stripped else "000000"


def f(val, default=0.0, nd=4):
    """安全浮点转换"""
    try:
        if val is None:
            return default
        v = float(val)
        return default if pd.isna(v) else round(v, nd)
    except Exception:
        return default


# ───────────────────────── /api/search ─────────────────────────
@app.get("/api/search")
def search(q: str = Query(..., min_length=1, description="代码或名称关键词")):
    try:
        df = ak.stock_info_a_code_name()
        q = q.strip()
        mask = df["code"].str.contains(q, na=False) | df["name"].str.contains(q, na=False)
        rows = df[mask].head(20)[["code", "name"]].to_dict("records")
        return {"code": 0, "data": rows}
    except Exception as e:
        logger.error("search: %s", e)
        raise HTTPException(500, detail=str(e))


# ───────────────────────── /api/spot ───────────────────────────
@app.get("/api/spot")
def spot(code: str = Query(..., description="股票代码")):
    try:
        sym = clean(code)
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == sym]
        if row.empty:
            raise HTTPException(404, detail=f"未找到 {sym}")
        r = row.iloc[0]
        data = {
            "code": sym,
            "name": str(r.get("名称", "")),
            "price": f(r.get("最新价")),
            "change": f(r.get("涨跌额")),
            "pct": f(r.get("涨跌幅")),
            "open": f(r.get("今开")),
            "high": f(r.get("最高")),
            "low": f(r.get("最低")),
            "pre_close": f(r.get("昨收")),
            "volume": f(r.get("成交量"), nd=0),
            "amount": f(r.get("成交额"), nd=0),
            "turnover": f(r.get("换手率")),
            "pe": f(r.get("市盈率-动态")),
            "pb": f(r.get("市净率")),
            "market_cap": f(r.get("总市值"), nd=0),
            "circ_cap": f(r.get("流通市值"), nd=0),
            "amplitude": f(r.get("振幅")),
            "vol_ratio": f(r.get("量比")),
            "bids": [],
            "asks": [],
        }
        try:
            ba = ak.stock_bid_ask_em(symbol=sym)
            if ba is not None and not ba.empty:
                bd = dict(zip(ba["item"], ba["value"]))
                for i in range(1, 6):
                    data["bids"].append({"price": f(bd.get(f"买{i}", 0)), "vol": f(bd.get(f"买{i}量", 0), nd=0)})
                    data["asks"].append({"price": f(bd.get(f"卖{i}", 0)), "vol": f(bd.get(f"卖{i}量", 0), nd=0)})
        except Exception as be:
            logger.warning("bid_ask: %s", be)
        return {"code": 0, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("spot: %s", e)
        raise HTTPException(500, detail=str(e))


# ───────────────────────── /api/timeline ───────────────────────
@app.get("/api/timeline")
def timeline(code: str = Query(...)):
    """分时图（今日分钟线 + 逐笔成交明细）"""
    try:
        sym = clean(code)
        minutes, trades = [], []

        # 1 分钟线 → 分时图
        try:
            dm = ak.stock_zh_a_hist_min_em(symbol=sym, period="1", adjust="")
            if dm is not None and not dm.empty:
                for _, row in dm.iterrows():
                    minutes.append({
                        "time": str(row.get("时间", row.get("日期", ""))),
                        "open": f(row["开盘"]),
                        "close": f(row["收盘"]),
                        "high": f(row["最高"]),
                        "low": f(row["最低"]),
                        "volume": f(row["成交量"], nd=0),
                        "amount": f(row.get("成交额", 0), nd=0),
                    })
        except Exception as me:
            logger.warning("minute1: %s", me)

        # 逐笔成交 → 成交明细
        try:
            dt = ak.stock_intraday_em(symbol=sym)
            if dt is not None and not dt.empty:
                for _, row in dt.tail(100).iterrows():
                    trades.append({
                        "time": str(row.get("时间", "")),
                        "price": f(row.get("成交价", 0)),
                        "vol": f(row.get("手数", 0), nd=0),
                        "dir": str(row.get("性质", "")),
                    })
        except Exception as te:
            logger.warning("intraday: %s", te)

        return {"code": 0, "data": {"minutes": minutes, "trades": trades}}
    except Exception as e:
        logger.error("timeline: %s", e)
        raise HTTPException(500, detail=str(e))


# ───────────────────────── /api/daily ──────────────────────────
@app.get("/api/daily")
def daily(code: str = Query(...), limit: int = Query(240, le=500)):
    try:
        sym = clean(code)
        df = ak.stock_zh_a_hist(symbol=sym, period="daily", adjust="qfq")
        if df is None or df.empty:
            return {"code": 0, "data": []}
        rows = []
        for _, r in df.tail(limit).iterrows():
            rows.append({
                "date": str(r["日期"]),
                "open": f(r["开盘"]),
                "close": f(r["收盘"]),
                "high": f(r["最高"]),
                "low": f(r["最低"]),
                "volume": f(r["成交量"], nd=0),
                "amount": f(r["成交额"], nd=0),
                "pct": f(r["涨跌幅"]),
            })
        return {"code": 0, "data": rows}
    except Exception as e:
        logger.error("daily: %s", e)
        raise HTTPException(500, detail=str(e))


# ───────────────────────── /api/minute ─────────────────────────
@app.get("/api/minute")
def minute(code: str = Query(...), period: str = Query("5", description="5/15/30/60")):
    try:
        sym = clean(code)
        p = period if period in {"1", "5", "15", "30", "60"} else "5"
        df = ak.stock_zh_a_hist_min_em(symbol=sym, period=p, adjust="qfq")
        if df is None or df.empty:
            return {"code": 0, "data": []}
        rows = []
        for _, r in df.tail(500).iterrows():
            rows.append({
                "time": str(r.get("时间", r.get("日期", ""))),
                "open": f(r["开盘"]),
                "close": f(r["收盘"]),
                "high": f(r["最高"]),
                "low": f(r["最低"]),
                "volume": f(r["成交量"], nd=0),
                "amount": f(r.get("成交额", 0), nd=0),
            })
        return {"code": 0, "data": rows}
    except Exception as e:
        logger.error("minute: %s", e)
        raise HTTPException(500, detail=str(e))


# ───────────────────────── /api/rank ───────────────────────────
@app.get("/api/rank")
def rank(type: str = Query("up", description="up/down/turnover/amount")):
    try:
        df = ak.stock_zh_a_spot_em()
        df = df.dropna(subset=["涨跌幅", "最新价"])
        sorts = {"up": ("涨跌幅", False), "down": ("涨跌幅", True), "turnover": ("换手率", False), "amount": ("成交额", False)}
        col, asc = sorts.get(type, ("涨跌幅", False))
        df = df.sort_values(col, ascending=asc).head(50)
        rows = []
        for _, r in df.iterrows():
            rows.append({
                "code": str(r["代码"]),
                "name": str(r["名称"]),
                "price": f(r.get("最新价")),
                "pct": f(r.get("涨跌幅")),
                "volume": f(r.get("成交量"), nd=0),
                "turnover": f(r.get("换手率")),
                "amount": f(r.get("成交额"), nd=0),
            })
        return {"code": 0, "data": rows}
    except Exception as e:
        logger.error("rank: %s", e)
        raise HTTPException(500, detail=str(e))


# ───────────────────────── /api/basic ──────────────────────────
@app.get("/api/basic")
def basic(code: str = Query(...)):
    try:
        sym = clean(code)
        df = ak.stock_individual_info_em(symbol=sym)
        if df is None or df.empty:
            return {"code": 0, "data": {}}
        d = {str(r["item"]): str(r["value"]) for _, r in df.iterrows()}
        return {"code": 0, "data": d}
    except Exception as e:
        logger.error("basic: %s", e)
        raise HTTPException(500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



