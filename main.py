import time
import pyupbit

from advanced_strategy import check_trend_condition, check_buy_condition, check_sell_condition
from config_loader import load_config
from upbit_api import place_market_buy, place_market_sell, get_krw_balance , get_balances

# ✅ 사용자 API 키 로드
cfg = load_config()
ACCESS_KEY = cfg["ACCESS_KEY"]
SECRET_KEY = cfg["SECRET_KEY"]

holding_dict = {}  # 보유 종목 → {"entry_price": float, "volume": float}
first_buy_done = False

print("🔁 자동매매 시작...")

balances = get_balances()
initial_krw = get_krw_balance()

print("\n📦 현재 보유 중인 종목:")
for b in balances:
    currency = b['currency']
    if currency == 'KRW':
        continue

    balance = float(b['balance'])
    avg_price = float(b.get('avg_buy_price', 0))

    if balance > 0 and avg_price > 0:
        ticker = f"KRW-{currency}"
        holding_dict[ticker] = {
            "entry_price": avg_price,
            "volume": balance
        }
        print(f" - {ticker}: 평단가 {avg_price:.2f}원, 보유량 {balance:.6f}개")

if not holding_dict:
    print("보유 중인 코인 없음.")


while True:
    traded_this_round = []
    tickers = pyupbit.get_tickers(fiat="KRW")
    krw = get_krw_balance()

    buy_candidates = []

    for ticker in tickers:
        if ticker not in holding_dict:
            if check_trend_condition(ticker) and check_buy_condition(ticker):
                buy_candidates.append(ticker)

    if buy_candidates and krw >= 5000:
        if krw >= initial_krw * 0.5:
            use_krw = krw * 0.5
            first_buy_done = True
        else:
            use_krw = krw

        each_amount = use_krw / len(buy_candidates)

        for ticker in buy_candidates:
            result = place_market_buy(ticker, each_amount * 0.995)
            if result:
                entry_price = float(result.get("price")) if result.get("price") else each_amount
                holding_dict[ticker] = {"entry_price": entry_price, "volume": result.get("volume",0), "buy_time": time.time()}
                traded_this_round.append(f"{ticker} 매수 진입")
                time.sleep(1)
                
    # 매도 조건 확인
    for ticker in list(holding_dict.keys()):
        data = holding_dict[ticker]
        entry_price = float(data["entry_price"])
        volume = data["volume"]
        buy_time = data.get("buy_time")
        if buy_time is None:
            # 이전 버전에서 만들어진 데이터 → 현재 시각으로 대체
            buy_time = time.time()
            holding_dict[ticker]["buy_time"] = buy_time

        if time.time() - buy_time < 300:
            continue

        action = check_sell_condition(ticker, entry_price)
            
        if action in ["loss", "full_profit", "macd_exit"]:
            result = place_market_sell(ticker, entry_price=entry_price)
            if result:
                traded_this_round.append(f"{ticker} 전량 청산: {action}")
                holding_dict.pop(ticker)
                time.sleep(1)

        elif action == "partial_profit":
            half_volume = volume * 0.5
            result = place_market_sell(ticker, volume=half_volume, entry_price=entry_price)
            if result:
                holding_dict[ticker]["volume"] = half_volume
                traded_this_round.append(f"{ticker} 50% 익절 완료")
                time.sleep(1)
    
    print("\n 이번 순회 요약:")
    if traded_this_round:
        for log in traded_this_round:
            print(" -", log)
    else:
        print("거래 없음.")

    print("\n 3분 후 다음 순회...")
    time.sleep(180)

