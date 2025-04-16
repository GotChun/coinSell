import time
from advanced_strategy import check_trend_condition, check_buy_condition, check_sell_condition
from config_loader import load_config
from upbit_api import place_market_buy, place_market_sell, get_krw_balance

# ✅ 사용자 API 키 로드
cfg = load_config()
ACCESS_KEY = cfg.ACCESS_KEY
SECRET_KEY = cfg.SECRET_KEY

# ✅ 모니터링할 종목 리스트
watchlist = ["KRW-1INCH",
"KRW-GAS",
"KRW-GAME2",
"KRW-GLM",
"KRW-G",
"KRW-GRS",
"KRW-CKB",
"KRW-NEO",
"KRW-XEM",
"KRW-NEAR",
"KRW-GRT",
"KRW-DOGE",
"KRW-DRIFT",
"KRW-MANA",
"KRW-DKA",
"KRW-ZRO",
"KRW-RENDER",
"KRW-LOOM",
"KRW-LSK",
"KRW-MASK",
"KRW-ME",
"KRW-MNT",
"KRW-EGLD",
"KRW-MED",
"KRW-META",
"KRW-MTL",
"KRW-MOC",
"KRW-MOCA",
"KRW-MOVE",
"KRW-MBL",
"KRW-MINA",
"KRW-MLK",
"KRW-VANA",
"KRW-AUCTION",
"KRW-VIRTUAL",
"KRW-BERA",
"KRW-BAT",
"KRW-BORA",
"KRW-BONK",
"KRW-BLAST",
"KRW-BLUR",
"KRW-VET",
"KRW-VTHO",
"KRW-BTC",
"KRW-BSV",
"KRW-BCH",
"KRW-BTT",
"KRW-BIGTIME",
"KRW-BEAM",
"KRW-SAND",
"KRW-SEI",
"KRW-SAFE",
"KRW-CELO",
"KRW-SONIC",
"KRW-SXP",
"KRW-SOL",
"KRW-LAYER"]
holding_dict = {}  # 보유 종목 → {"entry_price": float, "volume": float}

print("🔁 자동매매 시작...")

while True:
    traded_this_round = []

    for ticker in watchlist:
        print(f"\n📌 [{ticker}] 조건 검사 중...")

        # 보유 중이 아닐 때 → 매수 조건 검사
        if ticker not in holding_dict:
            if check_trend_condition(ticker) and check_buy_condition(ticker):
                krw = get_krw_balance()
                if krw >= 5000:
                    result = place_market_buy(ticker, krw * 0.995)
                    if result:
                        # 진입가 기록
                        entry_price = result.get("price") or krw / 2  # 테스트 시 가정
                        holding_dict[ticker] = {"entry_price": entry_price, "volume": result.get("volume", 0)}
                        traded_this_round.append(f"{ticker} 매수 진입")
                        time.sleep(1)
        else:
            # 보유 중이면 → 청산 조건 체크
            entry_price = holding_dict[ticker]["entry_price"]
            volume = holding_dict[ticker]["volume"]
            action = check_sell_condition(ticker, entry_price)

            if action in ["loss", "full_profit", "macd_exit"]:
                result = place_market_sell(ticker)
                if result:
                    traded_this_round.append(f"{ticker} 전량 청산: {action}")
                    holding_dict.pop(ticker)
                    time.sleep(1)

            elif action == "partial_profit":
                half_volume = volume * 0.5
                result = place_market_sell(ticker, half_volume)
                if result:
                    holding_dict[ticker]["volume"] = volume * 0.5  # 절반 유지
                    traded_this_round.append(f"{ticker} 50% 익절 완료")
                    time.sleep(1)

    # ✅ 순회 완료 후 결과 출력
    print("\n✅ 이번 순회 요약:")
    if traded_this_round:
        for log in traded_this_round:
            print(" -", log)
    else:
        print("거래 없음.")

    print("\n⏳ 5분 후 다음 순회...")
    time.sleep(300)  # 5분 대기
