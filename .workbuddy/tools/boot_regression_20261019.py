"""Boot entry regression against an isolated package and HTTP subtree.

Preserves the production app, all historical evidence, and the server root pointer.
"""
import argparse
import copy
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

os.environ['FT_BOOT_TEST_PACKAGE'] = 'com.ftproject.freedomtower.bootregression20261019c'
from boot_validation import Device, EVIDENCE, PACKAGE

ROOT = EVIDENCE / 'Regression/Final'
SERVER = EVIDENCE / 'Server'
POINTER = SERVER / 'Regression/release.json'
FAULTS = SERVER / 'faults.json'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def scenario(device, name, fallback=False):
    result = device.scenario('Regression/Final/' + name, '[BootSequence] GameReady', 60)
    log = (ROOT / name / 'logcat.txt').read_text(encoding='utf-8')
    stages = ['DLLReady', 'ResourcesVerified', 'Main', 'LoadingView', 'SplashView', 'GameReady']
    positions = [log.find('[BootSequence] ' + stage) for stage in stages]
    result['ordered'] = min(positions) >= 0 and positions == sorted(positions)
    result['local_fallback'] = 'Update unavailable; using verified local DLL set' in log
    result['passed'] = (result['matched'] and not result['issues'] and result['ordered']
                        and result['game_ready_count'] == 1 and (not fallback or result['local_fallback']))
    write(ROOT / name / 'result.json', result)
    if not result['passed']:
        raise RuntimeError('Failed regression: ' + name)
    return result


def matrix(device):
    baseline = json.loads((ROOT / 'baseline-release.json').read_text(encoding='utf-8'))
    original_pointer = POINTER.read_bytes()
    original_faults = FAULTS.read_bytes()
    results = []
    try:
        write(POINTER, baseline)
        write(FAULTS, {})
        device.adb('reverse', '--remove', 'tcp:18000', check=False)
        results.append(scenario(device, '50-first-offline'))
        device.adb('reverse', 'tcp:18000', 'tcp:18000')
        results.append(scenario(device, '51-online-no-update'))
        write(FAULTS, {'patterns': ['Regression/release.json'], 'status': 404})
        results.append(scenario(device, '52-release-404-local'))
        write(FAULTS, {'patterns': ['Regression/release.json'], 'delay': 4})
        results.append(scenario(device, '53-probe-timeout-local'))
        write(FAULTS, {})
        invalid = copy.deepcopy(baseline)
        invalid['aotSignature'] = '0' * 64
        write(POINTER, invalid)
        results.append(scenario(device, '54-incompatible-release-local', True))
        POINTER.write_text('{broken-release', encoding='utf-8')
        results.append(scenario(device, '55-malformed-release-local', True))
        broken_dll = copy.deepcopy(baseline)
        broken_dll['id'] += '-dll404'
        broken_dll['dlls'][0]['md5'] = '0' * 32
        write(POINTER, broken_dll)
        write(FAULTS, {'patterns': ['Regression/releases/*/HybridCLR/' + broken_dll['dlls'][0]['name']], 'status': 404})
        results.append(scenario(device, '56-dll-404-local', True))
        broken_dll['id'] += '-corrupt'
        write(POINTER, broken_dll)
        write(FAULTS, {'patterns': ['Regression/releases/*/HybridCLR/' + broken_dll['dlls'][0]['name']], 'corrupt': True})
        results.append(scenario(device, '57-dll-checksum-local', True))
        write(POINTER, baseline)
        write(FAULTS, {})
        device.adb('reverse', '--remove', 'tcp:18000')
        results.append(scenario(device, '58-offline-repeat'))
    finally:
        POINTER.write_bytes(original_pointer)
        FAULTS.write_bytes(original_faults)
        device.adb('reverse', 'tcp:18000', 'tcp:18000')
        write(ROOT / 'baseline-matrix.json', results)


def audit_http():
    base = 'http://127.0.0.1:18000/Regression/'
    release = json.load(urllib.request.urlopen(base + 'release.json', timeout=10))
    inventory = json.load(urllib.request.urlopen(base + release['contentRoot'] + '/payloads.json', timeout=10))
    checks = []
    for file in inventory['files']:
        data = urllib.request.urlopen(base + release['contentRoot'] + '/' + file['path'], timeout=15).read()
        checks.append({'path': file['path'], 'passed': len(data) == file['size'] and hashlib.md5(data).hexdigest() == file['md5']})
    result = {'release': release, 'checks': checks, 'failures': sum(not x['passed'] for x in checks)}
    write(ROOT / 'http-audit.json', result)
    if result['failures']:
        raise RuntimeError('HTTP payload integrity failed')
    print(json.dumps({'http_files': len(checks), 'failures': result['failures']}, ensure_ascii=False), flush=True)


def recovery(device):
    release = json.loads((ROOT / 'recovery-release.json').read_text(encoding='utf-8'))
    original_faults = FAULTS.read_bytes()
    try:
        write(POINTER, release)
        write(FAULTS, {'patterns': ['Regression/releases/*/FreeTower_' + release['resourceVersion'] + '.hash'], 'status': 404})
        blocked = device.scenario('Regression/Final/61-manifest-failure', 'HttpCode=404', 30)
        if not blocked['matched'] or blocked['game_ready_count'] or blocked['issues']:
            raise RuntimeError('Missing manifest was not blocked safely')
        write(FAULTS, {})
        device.adb('shell', 'input', 'tap', 935, 700)
        result = device.scenario('Regression/Final/62-manifest-retry-recovery', '[BootSequence] GameReady', 35, launch=False)
        if not result['matched'] or result['game_ready_count'] != 1 or result['issues']:
            raise RuntimeError('Visible retry did not recover')
        device.adb('reverse', '--remove', 'tcp:18000')
        scenario(device, '63-recovered-offline')
    finally:
        FAULTS.write_bytes(original_faults)
        device.adb('reverse', 'tcp:18000', 'tcp:18000')
    audit_http()


def audit_delivery():
    import zipfile
    apk = ROOT / 'boot-fixed-3.1.7.apk'
    baseline = json.loads((ROOT / 'baseline-release.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(apk) as archive:
        embedded = json.loads(archive.read('assets/boot-release.json'))
        if embedded != baseline:
            raise RuntimeError('APK baseline descriptor differs')
        for file in baseline['dlls']:
            if hashlib.md5(archive.read('assets/HybridCLR/' + file['name'])).hexdigest() != file['md5']:
                raise RuntimeError('APK DLL differs: ' + file['name'])
        manifest = archive.read('assets/yoo/FreeTower/FreeTower_' + baseline['resourceVersion'] + '.bytes')
        if hashlib.md5(manifest).hexdigest() != baseline['manifestMd5']:
            raise RuntimeError('APK manifest differs')
    checks = []
    for directory in sorted(ROOT.iterdir()):
        if not directory.is_dir() or not directory.name[:2].isdigit():
            continue
        path = directory / 'result.json'
        result = json.loads(path.read_text(encoding='utf-8'))
        passed = result['matched'] and not result['issues']
        if directory.name.startswith('61-'):
            passed = passed and result['game_ready_count'] == 0
        else:
            passed = passed and result['game_ready_count'] == 1
        checks.append({'scenario': directory.name, 'passed': passed, 'seconds': result['seconds']})
    result = {'package': PACKAGE, 'apk': str(apk), 'apk_bytes': apk.stat().st_size,
              'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(), 'baseline': baseline['id'],
              'checks': checks, 'failures': sum(not x['passed'] for x in checks)}
    write(ROOT / 'evidence-index.json', result)
    if len(checks) != 14 or result['failures']:
        raise RuntimeError('Expected 14 final scenarios without failures')
    print(json.dumps(result, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', required=True)
    parser.add_argument('--phase', choices=['matrix', 'update', 'recovery', 'audit'], required=True)
    args = parser.parse_args()
    device = Device(args.serial)
    if args.phase == 'matrix':
        matrix(device)
    elif args.phase == 'update':
        scenario(device, '59-online-resource-update')
        device.adb('reverse', '--remove', 'tcp:18000')
        try:
            scenario(device, '60-updated-offline')
        finally:
            device.adb('reverse', 'tcp:18000', 'tcp:18000')
        audit_http()
    elif args.phase == 'recovery':
        recovery(device)
    else:
        audit_http()
        audit_delivery()


if __name__ == '__main__':
    main()
