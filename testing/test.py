import pyupbit

# 테스트용 가짜 API 키 (실제 거래는 실패할 것)
ACCESS_KEY = "QfXX9776YETCLGfbxsMrVzf8jvfBLOPdFV1fiDAx"
SECRET_KEY = "5RWqRxxv3MjY7sbMP6wkqza2DmrjOSpcOyB7sRlL"

try:
    upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)
    print("[DEBUG] Upbit 객체 생성 성공")

    # 간단한 API 요청: 잔고 조회
    balances = upbit.get_balances()
    print("[DEBUG] 잔고 조회 결과:", balances)

except Exception as e:
    print("❌ [ERROR] API 호출 실패:", str(e))
