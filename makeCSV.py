import requests
import pandas as pd

url = "https://api.upbit.com/v1/market/all"
response = requests.get(url)
markets = response.json()

# KRW 마켓만 추출
krw_markets = [m for m in markets if m["market"].startswith("KRW-")]

# DataFrame으로 정리
df = pd.DataFrame(krw_markets)
df = df[["korean_name", "market"]]
df.columns = ["코인명", "티커"]
df = df.sort_values(by="코인명").reset_index(drop=True)

# CSV로 저장
df.to_csv("업비트_KRW_전체코인리스트.csv", index=False, encoding="utf-8-sig")
print("CSV 저장 완료!")
