from pathlib import Path
import subprocess
from safe_kiosk_people_agent.ble.hci import BleHciController, BleHciError

def test_ble_prepare_releases_stale_process_and_restarts_adapter(tmp_path: Path) -> None:
    usb=tmp_path/'usb'; usb.mkdir(); calls=[]
    def run(args, **kwargs):
        calls.append(args)
        out='hci1: Type: Primary\n        UP RUNNING PSCAN ISCAN\n' if args[:2]==('hciconfig','hci1') else ''
        return subprocess.CompletedProcess(args,0,out,'')
    status=BleHciController('hci1',usb,run).prepare()
    assert status.powered and status.discovering
    assert ('sudo','hciconfig','hci1','down') in calls
    assert ('sudo','pkill','-TERM','-f','bluetooth.*hci1') in calls
    assert ('sudo','hciconfig','hci1','reset') in calls

def test_ble_identity_fails_closed(tmp_path: Path) -> None:
    try: BleHciController('hci0',tmp_path/'missing').prepare()
    except BleHciError as exc: assert 'absent' in str(exc)
    else: raise AssertionError('expected identity failure')
