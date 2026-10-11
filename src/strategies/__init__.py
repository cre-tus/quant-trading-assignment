"""전략 플러그인 로더. config.yaml의 strategy.module 이름으로 로드한다."""
from importlib import import_module


def load_strategy(name: str):
    try:
        return import_module(f"src.strategies.{name}")
    except ModuleNotFoundError as e:
        raise SystemExit(
            f"[strategy] '{name}' 모듈을 찾을 수 없음. "
            f"src/strategies/ 안에 <{name}>.py가 있는지 확인하라."
        ) from e
