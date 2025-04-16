import pyupbit
import ta.trend
import pandas as pd

# 설정 값
TICKER = "KRW-STRAX"
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

# 기술 지표 추가
df["EMA200"] = ta.trend.EMAIndicator(close=df["HA_Close"], window=200).ema_indicator()
macd = ta.trend.MACD(close=df["HA_Close"])
df["MACD"] = macd.macd()
df["MACD_signal"] = macd.macd_signal()

# 백테스트 실행
cash = INITIAL_CASH
coin = 0
position = False
buy_price = 0
log = []

for i in range(200,len(df) -1):
    row = df.iloc[i]
    next_row = df.iloc[i+1]

    # 매수 조건
    recent = df.iloc[i-4 : i+1]
    over_ema = (recent["HA_Close"] > recent["EMA200"]).sum()
    golden_cross = df["MACD"].iloc[i-1] < df["MACD_signal"].iloc[i-1] and row["MACD"] > row["MACD_signal"]

    if not position and over_ema >= 2 and golden_cross:
        buy_price = next_row["open"]
        coin = cash / buy_price
        cash = 0
        position = True
        log.append({"time":next_row.name, "type":"buy", "price":buy_price, "asset":coin * buy_price})

    # 매도 조건
    dead_cross = df["MACD"].iloc[i-1] > df["MACD_signal"].iloc[i-1] and row["MACD"] < row["MACD_signal"]

    if position and dead_cross:
        sell_price = next_row["open"]
        cash = coin * sell_price
        log.append({"time":next_row.name, "type":"sell", "price":sell_price, "asset":cash})
        coin = 0
        position = False

final_asset = cash + coin * df.iloc[-1]["close"]
profit = final_asset - INITIAL_CASH
roi = (final_asset / INITIAL_CASH -1) * 100

# 결과 출력
print("\n===== 백테스트 결과 =====")
print(f"최종 자산: {int(final_asset)}원")
print(f"총 수익: {int(profit)}원")
print(f"수익률: {roi:.2f}%")

# 거래 로그 출력
log_df = pd.DataFrame(log)
print("\n[거래 내역]")
print(log_df)

# 필요하면 CSV 저장
# log_df.to_csv("doge_backtest_log.csv", index=False)  # 주석 해제 시 로그 저장


