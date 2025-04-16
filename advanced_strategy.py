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
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=200)
    if df is None or len(df) < 100:
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
    return trend_ok

# 📌 매수 조건 (5분봉 기준)
def check_buy_condition(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=300)
    if df is None or len(df) < 50:
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

    return golden_cross and stoch_rebound and ha_bullish and volume_jump

# 🚪 청산 조건 (익절, 손절, 데드크로스)
def check_sell_condition(ticker, entry_price):
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=5)
    current_price = df["close"].iloc[-1]

    # 손절: -3% 이상 손실
    if current_price <= entry_price * 0.97:
        return "loss"

    # 익절: +5% 수익
    if current_price >= entry_price * 1.05:
        # 추가로 1시간봉 추세 유지 여부 확인
        df_1h = pyupbit.get_ohlcv(ticker, interval="minute60", count=200)
        ema34 = ta.trend.ema_indicator(df_1h["close"], window=34).ema_indicator()
        if current_price > ema34.iloc[-1]:
            return "partial_profit"  # 50% 익절
        else:
            return "full_profit"  # 전량 익절

    # MACD 데드크로스 발생
    macd = ta.trend.MACD(df["close"], window_slow=34, window_fast=12, window_sign=13)
    if macd.macd().iloc[-2] > macd.macd_signal().iloc[-2] and macd.macd().iloc[-1] < macd.macd_signal().iloc[-1]:
        return "macd_exit"

    return None
