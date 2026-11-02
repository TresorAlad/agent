import json
from pathlib import Path
from typing import Any

from config import DATA_DIR


def _read_json(name: str) -> Any:
    path = DATA_DIR / name
    if not path.exists():
        return [] if name == "orders.json" else []
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(name: str, data: Any) -> None:
    path = DATA_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_catalog() -> list[dict]:
    return _read_json("catalog.json")


def load_stock() -> list[dict]:
    return _read_json("stock.json")


def save_stock(stock: list[dict]) -> None:
    _write_json("stock.json", stock)


def load_orders() -> list[dict]:
    return _read_json("orders.json")


def save_orders(orders: list[dict]) -> None:
    _write_json("orders.json", orders)
