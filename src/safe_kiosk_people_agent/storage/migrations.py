from __future__ import annotations

from importlib import resources
import sqlite3

def apply_migrations(connection: sqlite3.Connection, package: str) -> None:
    connection.execute("create table if not exists schema_version (version integer primary key, applied_at text not null default current_timestamp)")
    applied = {row[0] for row in connection.execute("select version from schema_version")}
    root = resources.files(package)
    for item in sorted(root.iterdir(), key=lambda x: x.name):
        if item.name.endswith(".sql") and item.name[:3].isdigit():
            version = int(item.name.split("_", 1)[0])
            if version in applied:
                continue
            connection.executescript(item.read_text())
            connection.execute("insert into schema_version(version) values (?)", (version,))
