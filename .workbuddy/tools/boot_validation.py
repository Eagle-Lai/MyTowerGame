"""ADB evidence helper scoped to the independent Boot validation application.

No uninstall, pm clear, or operations on the original game are performed.
"""
import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path

ADB = Path('C:/Users/Administrator/AppData/Local/Android/Sdk/platform-tools/adb.exe')
PACKAGE = os.environ.get('FT_BOOT_TEST_PACKAGE', 'com.ftproject.freedomtower.bootvalidation2')
ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'Builds/BootRefactor'


class Device:
    def __init__(self, serial):
        self.serial = serial

    def adb(self, *args, binary=False, check=True):
        result = subprocess.run([str(ADB), '-s', self.serial, *map(str, args)], capture_output=True, timeout=90)
        if check and result.returncode:
            raise RuntimeError(result.stderr.decode('utf-8', 'replace'))
        return result.stdout if binary else result.stdout.decode('utf-8', 'replace')

    def screenshot(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.adb('exec-out', 'screencap', '-p', binary=True))

    def start(self):
        self.adb('shell', 'am', 'force-stop', PACKAGE)
        self.adb('shell', 'monkey', '-p', PACKAGE, '-c', 'android.intent.category.LAUNCHER', '1')

    def log(self):
        pid = self.adb('shell', 'pidof', PACKAGE, check=False).strip()
        return self.adb('logcat', '-d', '-v', 'threadtime', '--pid=' + pid) if pid else ''

    def external(self):
        return '/sdcard/Android/data/' + PACKAGE + '/files'

    def override_server(self):
        local = EVIDENCE / 'server.txt'
        local.write_text('http://127.0.0.1:18000\n', encoding='utf-8')
        self.adb('shell', 'mkdir', '-p', self.external())
        self.adb('push', local, self.external() + '/server.txt')
        self.adb('reverse', 'tcp:18000', 'tcp:18000')

    def scenario(self, name, expected, timeout, launch=True):
        directory = EVIDENCE / name
        directory.mkdir(parents=True, exist_ok=True)
        started = time.time()
        if launch:
            self.start()
        self.screenshot(directory / 'initial.png')
        captured = set()
        log = ''
        while time.time() - started < timeout:
            log = self.log()
            for stage in ['LoadingView', 'SplashView', 'GameReady']:
                if '[BootSequence] ' + stage in log and stage not in captured:
                    self.screenshot(directory / (stage + '.png'))
                    captured.add(stage)
            if expected in log:
                break
            time.sleep(.5)
        self.screenshot(directory / 'result.png')
        (directory / 'logcat.txt').write_text(log, encoding='utf-8')
        sequence = re.findall(r'\[BootSequence\] ([^\r\n]+)', log)
        result = {'name': name, 'serial': self.serial, 'package': PACKAGE, 'expected': expected,
                  'matched': expected in log, 'seconds': round(time.time() - started, 2), 'sequence': sequence,
                  'issues': [line for line in log.splitlines() if any(token in line for token in
                              ['MissingMethodException', 'NullReferenceException', 'The referenced script',
                               'serialization layout', 'FATAL EXCEPTION', 'DllNotFoundException'])]}
        result['game_ready_count'] = log.count('[BootSequence] GameReady')
        result['config_attempts'] = re.findall(r'\[BootDiagnostics\] [^\r\n]+', log)
        result['release_logs'] = re.findall(r'\[Release\] [^\r\n]+', log)
        (directory / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--expect', default='[BootSequence] GameReady')
    parser.add_argument('--timeout', type=int, default=45)
    parser.add_argument('--continue-running', action='store_true')
    parser.add_argument('--set-server', action='store_true')
    args = parser.parse_args()
    device = Device(args.serial)
    if args.set_server:
        device.override_server()
    result = device.scenario(args.name, args.expect, args.timeout, not args.continue_running)
    raise SystemExit(0 if result['matched'] and not result['issues'] else 1)


if __name__ == '__main__':
    main()
