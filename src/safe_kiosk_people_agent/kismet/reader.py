from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from ..domain import KismetGeneration, KismetPacket, KismetCursor
class KismetReader:
    def __init__(self,path:Path): self.db=sqlite3.connect(path)
    def validate_schema(self,path:Path|None=None)->int:
        name = path or Path(self.db.execute("pragma database_list").fetchone()[2])
        tables={r[0] for r in self.db.execute("select name from sqlite_master where type='table'")}
        if 'packets' not in tables: raise sqlite3.DatabaseError(f"invalid Kismet schema: {name}")
        return 1
    def read_probe_requests(self,generation:KismetGeneration,after:KismetCursor|None=None,limit:int=10000):
        self.validate_schema()
        rows=self.db.execute("select rowid,ts_sec,ts_usec,sourcemac,signal_dbm,frequency,tags from packets where tags like '%DOT11_PROBE_REQ%' order by ts_sec,ts_usec,rowid limit ?",(limit,)).fetchall(); result=[]
        for row in rows:
            if after and (row[1],row[2],row[0]) <= (after.ts_sec,after.ts_usec,after.rowid): continue
            result.append(KismetPacket(generation.generation_id,row[0],row[1],row[2],datetime.fromtimestamp(row[1]+row[2]/1e6,timezone.utc),row[3],row[4],row[5]/1000,frozenset(str(row[6]).replace(',',' ').split())))
        return tuple(result)
    def is_at_eof(self,generation:KismetGeneration,cursor:KismetCursor)->bool:
        return not self.read_probe_requests(generation,cursor,1)
