import requests
import csv
import os
from datetime import datetime

def get_market_name_map(market_perfix="KRW"):
    """
    업비트에서 거래 가능한 마켓 코드와 한글명 매핑 딕셔너리 생성
    :param market_prefix: 'KRW', 'BTC', 'USDT' 중 선택
    :return: { "KRW-BTC": "비트코인", ... }
    """
    url = "https://api.upbit.com/v1/market/all"
    headers = {"accept": "application/json"}

    res = requests.get(url, headers=headers)
    data = res.json()

    market_dict = {
        item["market"]: item["korean_name"]
        for item in data
        if item["market"].startswith(market_perfix)
    }

    return market_dict

LOG_FILE = "trades.csv" # 거래 내역이 저장될 엑셀 파일
def log_trade(ticker, trade_type, price=None, volume=None, krw=None, entry_price=None, remaining_krw=None, profit_percent=None):

    #상세 거래 내역

    market_name_map = get_market_name_map()
    coin_name = market_name_map.get(ticker,ticker)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [now,
           coin_name,
           ticker,
           trade_type,
           price,
           volume,
           krw,
           entry_price if entry_price is not None else"",
           f"{profit_percent:.2f}%" if profit_percent is not None else "",
           remaining_krw if remaining_krw is not None else ""
           ]
    
    # 파일이 없으면 헤더 추가
    write_header = not os.path.exists(LOG_FILE)

    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["날짜/시간","종목명","티커","거래유형","가격","수량","금액","매수단가","수액률(%)","잔여KRW"])
        writer.writerow(row)

    print(f"📝 거래 내역 저장됨 → {coin_name} ({trade_type})")