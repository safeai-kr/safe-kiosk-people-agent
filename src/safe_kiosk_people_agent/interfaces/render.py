from ..config import WifiConfig
def render_link_rule(config:WifiConfig)->str:return f"[Match]\nPath={config.usb_id_path}\nPermanentMACAddress={config.permanent_mac}\n\n[Link]\nName=skwifi0\n"
def render_nm_unmanaged_dropin(config:WifiConfig)->str:return f"[keyfile]\nunmanaged-devices+=mac:{config.permanent_mac};interface-name:=skwifi0mon\n"
