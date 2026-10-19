"""Reproducible faults for the isolated Boot validation package/server only."""
import argparse
import copy
import json
import os
import shutil
import time
from pathlib import Path
from boot_validation import Device, EVIDENCE, PACKAGE

ROOT = EVIDENCE / 'Server'


def read_release(name):
    return json.loads((EVIDENCE / name).read_text(encoding='utf-8'))


def publish(release):
    (ROOT / 'release.json').write_text(json.dumps(release, indent=2), encoding='utf-8')


def fault(**values):
    (ROOT / 'faults.json').write_text(json.dumps(values), encoding='utf-8')


def clone(release, tag):
    release = copy.deepcopy(release)
    source = ROOT / release['contentRoot']
    release['id'] += '-' + tag
    release['contentRoot'] = 'releases/' + release['id']
    target = ROOT / release['contentRoot']
    if not target.exists():
        shutil.copytree(source, target, copy_function=os.link)
    fixtures = EVIDENCE / 'fixtures'
    fixtures.mkdir(exist_ok=True)
    (fixtures / (tag + '.json')).write_text(json.dumps(release, indent=2), encoding='utf-8')
    return release


def run(device, name, expected='[BootSequence] GameReady', timeout=60, launch=True):
    result = device.scenario(name, expected, timeout, launch)
    assert result['matched'] and not result['issues'], result
    if expected != '[BootSequence] GameReady':
        assert result['game_ready_count'] == 0, result
    return result


def retry(device):
    device.adb('shell', 'input', 'tap', 935, 700)


def wait_transfer(pattern, started, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for line in (EVIDENCE / 'requests.jsonl').read_text(encoding='utf-8').splitlines()[-150:]:
            event = json.loads(line)
            if event['time'] >= started and 'TRANSFER' in event['message'] and pattern in event['message']:
                return event
        time.sleep(.1)
    raise RuntimeError('No transfer: ' + pattern)


def command(device, value):
    assert PACKAGE == 'com.ftproject.freedomtower.bootvalidation2'
    device.adb('shell', f"run-as {PACKAGE} sh -c 'echo {value} > files/boot-validation-command.txt'")


def dll_tests(device):
    source = read_release('dll-v4-release.json')
    for name, settings in [
        ('18-dll-404', {'status': 404}),
        ('19-dll-checksum', {'corrupt': True}),
        ('20-dll-network-interruption', {'disconnect_after': 16384}),
    ]:
        release = clone(source, name)
        publish(release)
        fault(patterns=['releases/*/HybridCLR/FTProject.Runtime.dll'], **settings)
        run(device, name, '[Boot] Waiting for retry:', 95)
    release = clone(source, 'dll-kill')
    publish(release)
    fault(patterns=['releases/*/HybridCLR/FTProject.Runtime.dll'], kbps=32)
    started = time.time()
    device.start()
    wait_transfer('FTProject.Runtime.dll', started)
    time.sleep(2)
    directory = EVIDENCE / '21-dll-kill-restart'
    directory.mkdir(exist_ok=True)
    device.screenshot(directory / 'during-download.png')
    (directory / 'before-kill-logcat.txt').write_text(device.log(), encoding='utf-8')
    device.adb('shell', 'am', 'force-stop', PACKAGE)
    fault()
    run(device, '21-dll-kill-restart')


def ab_tests(device):
    publish(read_release('final-baseline-release.json'))
    fault()
    run(device, '22-prepare-baseline-for-ab')
    publish(read_release('ab-v4-release.json'))
    for name, settings in [
        ('23-ab-404', {'status': 404}),
        ('24-ab-corruption', {'corrupt': True}),
        ('25-ab-network-interruption', {'disconnect_after': 16384}),
    ]:
        fault(patterns=['releases/*/*.bundle'], **settings)
        run(device, name, '[Boot] Resource verification failed:', 65)
    fault(patterns=['releases/*/*.bundle'], kbps=32)
    started = time.time()
    retry(device)
    wait_transfer('.bundle', started)
    device.adb('shell', 'input', 'tap', 665, 700)
    time.sleep(1)
    directory = EVIDENCE / '26-ab-pause-resume-recovery'
    directory.mkdir(exist_ok=True)
    device.screenshot(directory / 'paused.png')
    assert '[BootSequence] Main' not in device.log()
    fault()
    device.adb('shell', 'input', 'tap', 665, 700)
    run(device, '26-ab-pause-resume-recovery', timeout=100, launch=False)


def combo_tests(device):
    publish(read_release('combo-release.json'))
    fault(patterns=['releases/*/*.bundle'], kbps=32)
    started = time.time()
    device.start()
    wait_transfer('.bundle', started)
    time.sleep(1)
    directory = EVIDENCE / '27-combined-kill-restart'
    directory.mkdir(exist_ok=True)
    device.screenshot(directory / 'during-download.png')
    log = device.log()
    (directory / 'before-kill-logcat.txt').write_text(log, encoding='utf-8')
    assert '[BootSequence] Main' not in log
    device.adb('shell', 'am', 'force-stop', PACKAGE)
    fault()
    run(device, '27-combined-kill-restart')
    command(device, 'config-retry')
    result = run(device, '28-config-transient-recovery')
    assert len(result['config_attempts']) == 3
    assert 'ok=False' in result['config_attempts'][0]
    assert 'ok=False' in result['config_attempts'][1]
    assert 'ok=True' in result['config_attempts'][2]
    assert all('bundleRefs=1' in item for item in result['config_attempts'])
    for tag in ['corrupt-cache', 'delete-cache']:
        command(device, tag)
        device.adb('reverse', '--remove', 'tcp:18000')
        try:
            run(device, '29-' + tag + '-offline-blocked', 'Offline resources incomplete:', 45)
        finally:
            device.adb('reverse', 'tcp:18000', 'tcp:18000')
        retry(device)
        run(device, '30-' + tag + '-same-version-repaired', launch=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['dll', 'ab', 'combo'])
    parser.add_argument('--serial', required=True)
    args = parser.parse_args()
    device = Device(args.serial)
    try:
        {'dll': dll_tests, 'ab': ab_tests, 'combo': combo_tests}[args.phase](device)
    finally:
        fault()


if __name__ == '__main__':
    main()
