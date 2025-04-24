import json
import os


# ✅ config.py를 런타임에 동적으로 로드하는 함수
def load_config():
    config_path = os.path.join(os.getcwd(),"config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError("config.json 파일을 찾을 수 없습니다.")
    with open(config_path,'r') as f:
        config = json.load(f)
    return config

