import time

import pyupbit
import pandas as pd
import ta

# ✅ 하이킨 아시 캔들 생성 함수 (공통으로 활용)
def get_heikin_ashi(df):
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    ha_open = [(df['open'].iloc[0] + df['close'].iloc[0]) / 2]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i - 1] + ha_df['HA_Close'].iloc[i - 1]) / 2)
    ha_df['HA_Open'] = ha_open
    ha_df['HA_High'] = ha_df[['HA_Open', 'HA_Close', 'high']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['HA_Open', 'HA_Close', 'low']].min(axis=1)
    return ha_df

# 📋 추세 필터 (1시간봉 기준)
def check_trend_condition(ticker):
    time.sleep(0.12)
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=200)
    if df is None or len(df) < 100:
        print(f"[{ticker}] ❌ 시세 데이터 없음 또는 부족")
        return False

    close = df["close"]
    ema34 = ta.trend.EMAIndicator(close=close, window=34).ema_indicator()
    ema89 = ta.trend.EMAIndicator(close=close, window=89).ema_indicator()
    macd = ta.trend.MACD(close)

    last_price = close.iloc[-1]
    trend_ok = (
        ema34.iloc[-1] > ema89.iloc[-1] and
        last_price > ema34.iloc[-1] and
        macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] and
        macd.macd_diff().iloc[-1] > 0
    )
    if trend_ok:
        print(f"[{ticker}] 📈 추세 조건 통과!")
    else:
        print(f"[{ticker}] ⚠️ 추세 조건 불충분")

    return trend_ok

# 📌 매수 조건 (5분봉 기준)
def check_buy_condition(ticker):
    time.sleep(0.12)
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=300)
    if df is None or len(df) < 50:
        print(f"[{ticker}] ❌ 매수조건용 시세 데이터 없음.")
        return False

    # MACD 골든크로스
    macd = ta.trend.MACD(df["close"], window_slow=34, window_fast=12, window_sign=13)
    macd_cross = df["macd"] = macd.macd()
    macd_signal = df["macd_signal"] = macd.macd_signal()
    golden_cross = macd_cross.iloc[-2] < macd_signal.iloc[-2] and macd_cross.iloc[-1] > macd_signal.iloc[-1]

    # Stochastic RSI 반등
    stoch = ta.momentum.StochRSIIndicator(df["close"])
    k = stoch.stochrsi_k()
    stoch_rebound = k.iloc[-2] < 0.2 and k.iloc[-1] > 0.3

    # Heikin-Ashi 양봉 전환
    ha_df = get_heikin_ashi(df)
    ha_bullish = ha_df["HA_Close"].iloc[-2] < ha_df["HA_Open"].iloc[-2] and ha_df["HA_Close"].iloc[-1] > ha_df["HA_Open"].iloc[-1]

    # 거래량 증가
    avg_volume = df["volume"].iloc[-21:-1].mean()
    volume_jump = df["volume"].iloc[-1] > avg_volume * 1.3

    all_conditions = golden_cross and stoch_rebound and ha_bullish and volume_jump
    print(f"[{ticker}] {'🟢' if all_conditions else '⚠️'} 매수 조건 {'충족' if all_conditions else '미충족'}\n")
    print(f"[{ticker}] MACD 골든크로스: {golden_cross}")
    print(f"[{ticker}] Stoch RSI 반등: {stoch_rebound}")
    print(f"[{ticker}] Heikin-Ashi 양봉 전환: {ha_bullish}")
    print(f"[{ticker}] 거래량 증가: {volume_jump}")

    return golden_cross and stoch_rebound and ha_bullish and volume_jump

# 🚪 청산 조건 (익절, 손절, 데드크로스)
def check_sell_condition(ticker, entry_price,partial_profit_done=False):
    time.sleep(0.12)
    # df = pyupbit.get_ohlcv(ticker, interval="minute5", count=300)

    #실시간 현재가 조회
    current_price = pyupbit.get_current_price(ticker)   # 종목의 현재가를 조회
    if current_price is None:
        print(f"[{ticker}] 현재가 조회 실패.")
        return None

    print(f"[{ticker}] 현재가: {current_price}, 매수가: {entry_price}, partial_profit_done: {partial_profit_done}")

    if not partial_profit_done:

        # 익절: +5% 수익
        if current_price >= entry_price * 1.05:
            # 추가로 1시간봉 추세 유지 여부 확인
            df_1h = pyupbit.get_ohlcv(ticker, interval="minute60", count=200)
            # ema_indicator = ta.trend.EMAIndicator(close=df_1h["close"], window=34)
            ema34 = ta.trend.EMAIndicator(close=df_1h['close'], window=34).ema_indicator()
            if current_price > ema34.iloc[-1]:
                return "partial_profit"  # 50% 익절
            else:
                return "full_profit"  # 전량 익절

    # 손절: -3% 이상 손실
    if current_price <= entry_price * 0.97:
        return "loss"

    # MACD 데드크로스 체크 (5분봉 기준)
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=300)
    if df is None or len(df) < 50:
        print(f"[{ticker}] ❌ MACD 확인용 시세 데이터 부족.")
        return None

    macd = ta.trend.MACD(df['close'], window_slow=34, window_fast=12, window_sign=13)
    if macd.macd().iloc[-2] > macd.macd_signal().iloc[-2] and macd.macd().iloc[-1] < macd.macd_signal().iloc[-1]:
        return "macd_exit"

    return None
