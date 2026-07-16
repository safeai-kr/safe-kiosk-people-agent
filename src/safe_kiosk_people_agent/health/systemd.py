from __future__ import annotations
import os
import re
import socket

class SystemdNotifier:
    def __init__(self, notify_socket: str|None=None) -> None: self.address=notify_socket or os.getenv("NOTIFY_SOCKET")
    def _send(self, payload:str) -> None:
        if not self.address: return
        address=self.address
        if address.startswith("@"): address="\0"+address[1:]
        sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        try: sock.connect(address); sock.sendall(payload.encode())
        finally: sock.close()
    def ready(self,detail:str)->None:self._send("READY=1")
    def reloading(self,detail:str)->None:self._send("RELOADING=1")
    def watchdog(self,detail:str)->None:self._send("WATCHDOG=1")
    def status(self,detail:str)->None:self._send("STATUS="+re.sub(r"[\r\n]"," ",detail)[:512])
