
import pyupbit
import ta
import pandas as pd
import requests
from ta.trend import EMAIndicator

INITIAL_CASH = 1_000_000
RESULTS = []
print("모든 종목 백테스팅 진행 중...")
# 한글 이름 매핑 생성
def get_market_name_map(market_prefix="KRW"):
    url = "https://api.upbit.com/v1/market/all"
    headers = {"accept": "application/json"}
    res = requests.get(url, headers=headers)
    data = res.json()
    return {
        item["market"]: item["korean_name"]
        for item in data
        if item["market"].startswith(market_prefix)
    }

name_map = get_market_name_map()
tickers = list(name_map.keys())

for TICKER in tickers:
    try:
        df = pyupbit.get_ohlcv(TICKER, interval="minute5", count=1440).copy()
        if df is None or len(df) < 300:
            continue

        df["HA_Close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
        ha_open = [(df["open"].iloc[0] + df["close"].iloc[0]) / 2]
        for i in range(1, len(df)):
            ha_open.append((ha_open[i - 1] + df["HA_Close"].iloc[i - 1]) / 2)
        df["HA_Open"] = ha_open
        ema34 = EMAIndicator(close=df["close"], window=34)
        ema89 = EMAIndicator(close=df["close"], window=89)

        df["EMA34"] = ema34.ema_indicator()
        df["EMA89"] = ema89.ema_indicator()
        macd = ta.trend.MACD(df["close"], window_fast=12, window_slow=34, window_sign=13)
        df["MACD"] = macd.macd()
        df["MACD_signal"] = macd.macd_signal()
        df["MACD_diff"] = macd.macd_diff()

        cash = INITIAL_CASH
        coin = 0
        position = False
        buy_price = 0
        peak = INITIAL_CASH
        max_drawdown = 0
        win_count = 0
        trade_count = 0

        for i in range(89, len(df) - 1):
            row = df.iloc[i]
            next_row = df.iloc[i + 1]
            last_price = row["close"]

            trend_ok = (
                row["EMA34"] > row["EMA89"]
                and last_price > row["EMA34"]
                and row["MACD"] > row["MACD_signal"]
                and row["MACD_diff"] > 0
            )

            golden_cross = df["MACD"].iloc[i - 1] < df["MACD_signal"].iloc[i - 1] and row["MACD"] > row["MACD_signal"]
            if not position and trend_ok and golden_cross:
                buy_price = next_row["open"]
                coin = cash / buy_price
                cash = 0
                position = True

            if position:
                current_value = coin * last_price
                drawdown = (peak - current_value) / peak
                max_drawdown = max(max_drawdown, drawdown)

                profit_rate = (last_price / buy_price - 1) * 100
                dead_cross = df["MACD"].iloc[i - 1] > df["MACD_signal"].iloc[i - 1] and row["MACD"] < row["MACD_signal"]

                if profit_rate <= -3 or profit_rate >= 5 or dead_cross:
                    sell_price = next_row["open"]
                    cash = coin * sell_price
                    coin = 0
                    position = False
                    trade_count += 1
                    if sell_price > buy_price:
                        win_count += 1
                    peak = max(peak, cash)

        final_asset = cash + coin * df.iloc[-1]["close"]
        profit = final_asset - INITIAL_CASH
        roi = (final_asset / INITIAL_CASH - 1) * 100
        win_rate = (win_count / trade_count) * 100 if trade_count else 0

        RESULTS.append({
            "티커": TICKER,
            "코인명": name_map.get(TICKER, ""),
            "최종 자산": int(final_asset),
            "총 수익": int(profit),
            "수익률(%)": round(roi, 2),
            "거래 수": trade_count,
            "승리 수": win_count,
            "승률(%)": round(win_rate, 2),
            "최대 낙폭(%)": round(max_drawdown * 100, 2)
        })
    except Exception as e:
        print(f"⚠️ {TICKER} 백테스트 중 오류 발생: {e}")
        continue

df_result = pd.DataFrame(RESULTS)
df_result.to_csv("backtest.csv", index=False, encoding="utf-8-sig")
print("\n✅ 모든 백테스트 완료. 결과는 backtest.csv 파일에 저장됨.")
