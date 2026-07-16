from __future__ import annotations
import argparse
from pathlib import Path
from .config import load_config

def main() -> None:
    parser = argparse.ArgumentParser(prog="people-agent")
    parser.add_argument("--config", type=Path)
    parser.add_argument("command", nargs="?", default="check-config")
    args = parser.parse_args()
    if args.command == "check-config":
        if args.config is None: parser.error("--config is required")
        config = load_config(args.config)
        print(f"config_digest={__import__('safe_kiosk_people_agent.config', fromlist=['config_digest']).config_digest(config)}")
