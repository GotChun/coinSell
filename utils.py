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
def log_trade(ticker,trade_type, price=None, volume=None, krw=None):
    """
    거래 내역을 CSV로 저장
    :param ticker: KRW-BTC
    :param trade_type: "매수" 또는 "매도"
    :param price: 체결 가격 (옵션)
    :param volume: 수량 (옵션)
    :param krw: 총 금액 (옵션)
    """
    market_name_map = get_market_name_map()
    coin_name = market_name_map.get(ticker,ticker)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [now,coin_name,ticker,trade_type,price,volume,krw]
    
    # 파일이 없으면 헤더 추가
    write_header = not os.path.exists(LOG_FILE)

    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["날짜/시간","종목명","티커","거래유형","가격","수량","금액"])
        writer.writerow(row)

    print(f"📝 거래 내역 저장됨 → {coin_name} ({trade_type})")