# strategy.py

import pyupbit
import pandas as pd
import ta

def get_heikin_ashi(df):    #하이킨아시 캔들 변환 함수
    """하이킨아시 캔들로 변환"""
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4 #시가 + 고가 + 저가 + 종가 / 4 = 평균값

    # 첫번째 값을 .iloc로 접근
    ha_open = [(df['open'].iloc[0] + df['close'].iloc[0]) / 2]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i - 1] + ha_df['HA_Close'].iloc[i - 1]) / 2)
    ha_df['HA_Open'] = ha_open

    ha_df['HA_High'] = ha_df[['HA_Open', 'HA_Close', 'high']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['HA_Open', 'HA_Close', 'low']].min(axis=1)
    return ha_df

def check_buy_condition(ticker="KRW-BTC"):
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=300)  # 1시간 기준, 최근 300개의 시세 데이터
    if df is None or len(df) < 200:
        print("데이터가 부족합니다.")
        return False

    # 하이킨아시 캔들 변환
    ha_df = get_heikin_ashi(df)

    # EMA200 계산 (ta 라이브러리의 EMAIndicator 사용)
    ema_indicator = ta.trend.EMAIndicator(close=ha_df['HA_Close'], window=200)
    ha_df['EMA200'] = ema_indicator.ema_indicator()

    # 최근 5개 하이킨아시 캔들이 EMA200 위에 있는지 체크
    recent_ha = ha_df[-5:]
    over_ema = recent_ha[recent_ha['HA_Close'] > recent_ha['EMA200']]
    if len(over_ema) < 2:
        print("조건1 실패: EMA200 위에 있는 캔들이 2개 미만")
        return False

    # MACD 계산 (ta 라이브러리의 MACD 클래스 사용)
    macd_indicator = ta.trend.MACD(close=ha_df['HA_Close'])
    ha_df['macd'] = macd_indicator.macd()
    ha_df['macd_signal'] = macd_indicator.macd_signal()

    # 최근 3개 캔들에서 MACD 골든크로스 발생 여부 확인
    last = ha_df.iloc[-3:]
    if (last['macd'].iloc[-2] < last['macd_signal'].iloc[-2]) and \
       (last['macd'].iloc[-1] > last['macd_signal'].iloc[-1]):
        print("조건2 통과 ✅ (EMA200 위 + MACD 골든크로스)")
        return True
    else:
        print("조건2 실패: MACD 골든크로스 없음")
        return False

def check_sell_condition(ticker="KRW-BTC"):
    """MACD 데드크로스 발생 여부 체크"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60",count=300)
    if df is None or len(df) < 50:
        print("데이터가 부족합니다.")
        return False

    # 하이킨아시 변환
    ha_df = get_heikin_ashi(df)

    #MACD 계산
    macd_indicator = ta.trend.MACD(close=ha_df['HA_Close'])
    ha_df['macd'] = macd_indicator.macd()
    ha_df['macd_signal'] = macd_indicator.macd_signal()

    last = ha_df.iloc[-3:]
    
    # 데드크로스 발생 여부
    if (last['macd'].iloc[-2] > last['macd_signal'].iloc[-2]) and \
        (last['macd'].iloc[-1] < last['macd_signal'].iloc[-1]):
        print("✅ 조건2 통과 (MACD 데드크로스)")
        return True
    else:
        print("❌ 조건2 실패: 데드크로스 아님")
        return False