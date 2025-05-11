from upbit_api import place_market_buy, get_krw_balance, get_balances, place_market_sell


def test_buy_condition(ticker):
    print(f"테스트 코드 작성..{ticker}")
    return True

# def main():
#     ticker = "KRW-DOGE"
#     krw = get_krw_balance()
#     print(f"잔고확인. 현재 KRW 잔액: {krw:.2f}")
#
#     if krw < 6000:
#         print("최소 잔액 부족함 (최소 6000원 이상)")
#         return
#
#     if test_buy_condition(ticker):
#         amount = 5500
#         print(f"[매수 테스트] {ticker} 코인 {amount} KRW 어치 매수 시도")
#         result = place_market_buy(ticker, amount)
#
#         print("[매수 결과 확인]")
#         print(result)
#
# if __name__ == "__main__":
#     main()


# 매도 테스트

def main():
    ticker = "KRW-DOGE"

    # 현재 보유 수량 및 평단가 확인
    balances = get_balances()
    coin = ticker.split("-")[1]
    entry_price = 5500
    volume = 1

    for b in balances:
        if b['currency'] == coin:
            entry_price = float(b.get("avg_buy_price", 0))
            volume = float(b.get("balance", 0))
            break

    if not volume or volume <= 0:
        print(f"❌ 매도 테스트 불가: 현재 보유한 {coin} 수량이 없습니다.")
        return

    print(f"[매도 테스트] {ticker} 매도 시도 - 수량: {volume:.6f}, 평단가: {entry_price:.2f}")

    result = place_market_sell(ticker, volume=volume, entry_price=entry_price)
    print("[매도 결과]")
    print(result)


if __name__ == "__main__":
    main()