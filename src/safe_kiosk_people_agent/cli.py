from __future__ import annotations
import argparse
import json
from pathlib import Path
from .commands.check_config import check_config
from .commands.inspect_signals import inspect_signals
from .commands.reload_config import reload_config

def main() -> None:
    parser = argparse.ArgumentParser(prog="people-agent")
    parser.add_argument("--config", type=Path)
    parser.add_argument("command", nargs="?", default="check-config", choices=['check-config','inspect-signals','reload-config'])
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--source', default='both')
    parser.add_argument('--window-seconds', type=int, default=300)
    parser.add_argument('--format', choices=['text','json'], default='text')
    args = parser.parse_args()
    if args.command == "check-config":
        if args.config is None: parser.error("--config is required")
        if args.command=='check-config':
            print(json.dumps(check_config(args.config),sort_keys=True)); return
        if args.command=='reload-config':
            if args.candidate is None: parser.error('--candidate is required')
            print(json.dumps(reload_config(args.candidate),sort_keys=True)); return
        output=inspect_signals(args.source,args.window_seconds,args.format)
        print(json.dumps(output,sort_keys=True) if args.format=='json' else output)
