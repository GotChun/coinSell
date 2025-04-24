import pyupbit
import ta.trend
import pandas as pd

# 설정 값
TICKER = "KRW-DOGE"
COUNT = 720     #1시간 봉 30일치
INITIAL_CASH = 1_000_000

# 데이터 수집
df = pyupbit.get_ohlcv(TICKER,interval="minute60",count=COUNT).copy()

# 하이킨아시 캔들 생성
df["HA_Close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
ha_open = [(df["open"]).iloc[0] + df["close"].iloc[0] /2]
for i in range(1,len(df)):
    ha_open.append((ha_open[i-1] + df["HA_Close"].iloc[i-1]) / 2)
df["HA_Open"] = ha_open
df["HA_High"] = df[["HA_Open" , "HA_Close","high"]].max(axis=1)
df["HA_Low"] = df[["HA_Open","HA_Close","low"]].min(axis=1)

# 기술 지표
df["EMA34"] = ta.trend.EMAIndicator(df["close"], window=34).ema_indicator()
df["EMA89"] = ta.trend.EMAIndicator(df["close"], window=89).ema_indicator()
macd = ta.trend.MACD(df["close"], window_fast=12, window_slow=34, window_sign=13)
df["MACD"] = macd.macd()
df["MACD_signal"] = macd.macd_signal()
df["MACD_diff"] = macd.macd_diff()


# 백테스트 실행
cash = INITIAL_CASH
coin = 0
position = False
buy_price = 0
log = []
peak = INITIAL_CASH
max_drawdown = 0
win_count = 0
trade_count = 0

for i in range(89,len(df) -1):
    row = df.iloc[i]
    next_row = df.iloc[i+1]
    last_price = row["close"]

    # 추세 조건
    trend_ok = (
        row["EMA34"] > row["EMA89"]
        and last_price > row["EMA34"]
        and row["MACD"] > row["MACD_signal"]
        and row["MACD_diff"] > 0
    )

    # 매수 조건
    golden_cross = df["MACD"].iloc[i - 1] < df["MACD_signal"].iloc[i - 1] and row["MACD"] > row["MACD_signal"]
    if not position and trend_ok and golden_cross:
        buy_price = next_row["open"]
        coin = cash / buy_price
        cash = 0
        position = True
        asset = coin * buy_price
        log.append({"time": next_row.name, "type": "buy", "price": buy_price, "asset": asset})

    # 매도 조건
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
            asset = cash
            log.append({"time": next_row.name, "type": "sell", "price": sell_price, "asset": asset})
            trade_count += 1
            if sell_price > buy_price:
                win_count += 1
            peak = max(peak, asset)

final_asset = cash + coin * df.iloc[-1]["close"]
profit = final_asset - INITIAL_CASH
roi = (final_asset / INITIAL_CASH -1) * 100
win_rate = (win_count / trade_count) * 100 if trade_count else 0

print("\n===== 백테스트 결과 =====")
print(f"최종 자산: {int(final_asset)}원")
print(f"총 수익: {int(profit)}원")
print(f"수익률: {roi:.2f}%")
print(f"총 거래 횟수: {trade_count}회")
print(f"승리 횟수: {win_count}회")
print(f"승률: {win_rate:.2f}%")
print(f"최대 낙폭: {max_drawdown * 100:.2f}%")

log_df = pd.DataFrame(log)
print("\n[거래 내역]")
print(log_df)

# 필요하면 CSV 저장
# log_df.to_csv("doge_backtest_log.csv", index=False)  # 주석 해제 시 로그 저장


