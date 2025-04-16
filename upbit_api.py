# 업비트 API 연동 모듈

import pyupbit
from config import ACCESS_KEY,SECRET_KEY
from utils import log_trade

upbit = pyupbit.Upbit(ACCESS_KEY,SECRET_KEY)

def get_balances():
    """"보유 자산 목록을 가져옵니다."""
    balances = upbit.get_balances() #보유 자산 목록 조회
    for b in balances:
        print(f"{b['currency']}:{b['balance']}개 (평단가: {b.get('avg_buy_price','없음')})")
    return balances

def place_market_buy(ticker,amount):
    """보유한 KRW 전액으로 시장가 매수 (수수료 고려 99.5%)"""
    print(f"[매수] {ticker} 코인을 {int(amount)}원 어치 시장가 매수합니다.")

    # 실제 거래 막고 테스트만 할 경우:
    # result = {"price": None, "volume": None, "test": True}

    # 실제 거래용
    result = upbit.buy_market_order(ticker,amount)
    print("매수 완료",result)
    
    log_trade(
        ticker=ticker,
        trade_type="매수",
        price=result.get("price"),
        volume=result.get("volume"),
        krw=amount
    )
    
    return result

def place_market_sell(ticker):
    """보유한 코인을 전량 시장가 매도 (수수료 고려 99.5%)"""
    balances = upbit.get_balances()
    coin = ticker.split('-')[1]  # "KRW-BTC" → "BTC"

    for b in balances:
        if b['currency'] == coin:
            volume = float(b['balance'])
            if volume > 0:
                sell_volume = volume * 0.995  # 수수료 여유
                print(f"[매도] {ticker} 시장가 매도: 수량 {sell_volume:.8f}")
                result = upbit.sell_market_order(ticker, sell_volume)
                # return {"test": True}
                # 로그 기록
                log_trade(
                    ticker=ticker,
                    trade_type="매도",
                    price=result.get("price"),
                    volume=result.get("volume"),
                    krw=None  # 필요하면 계산 가능
                )

                return result

    print("❌ 매도 실패: 보유 수량 없음")
    return None

def get_krw_balance():
    """현재 KRW 잔액 조회 함수"""
    balances = upbit.get_balances()
    krw = next((float(b['balance']) for b in balances if b['currency'] == 'KRW'),0)
    return krw
