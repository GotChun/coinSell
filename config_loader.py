import importlib.util
import os

# ✅ config.py를 런타임에 동적으로 로드하는 함수
def load_config():
    path = os.path.join(os.path.dirname(__file__), "config.py")
    spec = importlib.util.spec_from_file_location("config", path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config
