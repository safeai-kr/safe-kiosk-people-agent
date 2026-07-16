from typing import NoReturn

def main_wifi() -> NoReturn: raise SystemExit("wifi collector requires installation configuration")
def main_ble() -> NoReturn: raise SystemExit("ble collector requires installation configuration")
def main_metrics() -> None:
    raise SystemExit("metrics service requires installation configuration")
def main_recover() -> NoReturn: raise SystemExit("recovery worker requires --scope wifi|ble")
