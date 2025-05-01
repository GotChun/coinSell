# 업비트 API 연동 모듈
import time

import pyupbit
from config_loader import load_config
from utils import log_trade

cfg = load_config()
ACCESS_KEY = cfg["ACCESS_KEY"]
SECRET_KEY = cfg["SECRET_KEY"]

upbit = pyupbit.Upbit(ACCESS_KEY,SECRET_KEY)

def get_balances():
    """"보유 자산 목록을 가져옵니다."""
    balances = upbit.get_balances() #보유 자산 목록 조회
    print("balances : ", balances)
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

    time.sleep(1.2)
    balances = get_balances()
    coin = ticker.split("-")[1]

    entry_price = 0
    volume = 0
    for b in balances:
        if b['currency'] == coin:
            entry_price = float(b.get("avg_buy_price", 0))
            volume = float(b.get("balance", 0))
            break

    remaining_krw = get_krw_balance() # 매수 후에 잔고 다시 조회
    log_trade(
        ticker=ticker,
        trade_type="매수",
        price=entry_price,
        volume=volume,
        krw=amount,
        remaining_krw=remaining_krw
    )
    
    return result

def place_market_sell(ticker,volume=None, entry_price=None):
    balances = upbit.get_balances()
    coin = ticker.split('-')[1]  # "KRW-BTC" → "BTC"

    for b in balances:
        if b['currency'] == coin:
            total_volume = float(b['balance'])

            if total_volume > 0:
                sell_volume = volume if volume else total_volume # 전량 또는 일부
                print(f"[매도] {ticker} 시장가 매도: 수량 {sell_volume:.8f}")
                result = upbit.sell_market_order(ticker,sell_volume)

                # 매도 후 잔액 조회 및 수익률 계산
                sell_price =result.get("price") or 0
                remaining_krw = get_krw_balance()
                profit_percent = ((sell_price - entry_price) * 100 if entry_price else None)

                # 거래 로그 저장
                log_trade(
                    ticker=ticker,
                    trade_type="매도",
                    price=sell_price,
                    volume=result.get("volume"),
                    krw=None,
                    entry_price=entry_price,
                    remaining_krw=remaining_krw,
                    profit_percent=profit_percent
                )

                return {
                    "price": entry_price,
                    "volume": volume,
                    "raw": result
                }

    print("❌ 매도 실패: 보유 수량 없음")
    return None

def get_krw_balance():
    """현재 KRW 잔액 조회 함수"""
    balances = upbit.get_balances()
    krw = next((float(b['balance']) for b in balances if b['currency'] == 'KRW'),0)
    return krw
