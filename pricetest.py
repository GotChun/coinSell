from upbit_api import place_market_buy, get_krw_balance


def test_buy_condition(ticker):
    print(f"테스트 코드 작성..{ticker}")
    return True

def main():
    ticker = "KRW-DOGE"
    krw = get_krw_balance()
    print(f"잔고확인. 현재 KRW 잔액: {krw:.2f}")

    if krw < 6000:
        print("최소 잔액 부족함 (최소 6000원 이상)")
        return

    if test_buy_condition(ticker):
        amount = 5500
        print(f"[매수 테스트] {ticker} 코인 {amount} KRW 어치 매수 시도")
        result = place_market_buy(ticker, amount)

        print("[매수 결과 확인]")
        print(result)

if __name__ == "__main__":
    main()
