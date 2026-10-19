"""Recheck saved scenario outcomes and every byte of the isolated final HTTP release."""
import hashlib
import json
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'Builds/BootRefactor'
URL = 'http://127.0.0.1:18000'


def fetch(relative):
    with urllib.request.urlopen(URL + '/' + relative, timeout=10) as response:
        return response.read()


def main():
    results = []
    failures = []
    ignored = {'17-manifest-missing': 'Initial assertion text did not match; corrected and rerun as 17b.'}
    for folder in sorted(EVIDENCE.iterdir()):
        if not folder.is_dir() or not re.match(r'^(1[0-9]|2[0-9]|3[0-9]|41)', folder.name):
            continue
        path = folder / 'result.json'
        if not path.exists() or folder.name in ignored:
            continue
        result = json.loads(path.read_text(encoding='utf-8'))
        if not result['matched'] or result['issues']:
            failures.append(folder.name + ': expectation or issue check failed')
        if result['expected'] == '[BootSequence] GameReady':
            sequence = result['sequence']
            if result['game_ready_count'] != 1 or sequence.count('SplashView') != 1:
                failures.append(folder.name + ': repeated or missing completion')
            if not sequence.index('Main') < sequence.index('LoadingView') < sequence.index('SplashView') < sequence.index('GameReady'):
                failures.append(folder.name + ': invalid sequence')
        elif result['game_ready_count'] or 'Main' in result['sequence']:
            failures.append(folder.name + ': failure incorrectly entered Main')
        results.append(result)
    descriptor_bytes = fetch('release.json')
    descriptor = json.loads(descriptor_bytes)
    content = descriptor['contentRoot']
    inventory = json.loads(fetch(content + '/payloads.json'))
    served = []
    for entry in inventory['files']:
        payload = fetch(content + '/' + entry['path'])
        ok = len(payload) == entry['size'] and hashlib.md5(payload).hexdigest() == entry['md5']
        served.append({'path': entry['path'], 'size': len(payload), 'md5': hashlib.md5(payload).hexdigest(), 'ok': ok})
        if not ok:
            failures.append('HTTP payload mismatch: ' + entry['path'])
    if json.loads(fetch(content + '/release.json')) != descriptor:
        failures.append('Immutable descriptor differs from activation pointer')
    apk = EVIDENCE / 'final-clean.apk'
    with zipfile.ZipFile(apk) as archive:
        baseline_name = next(name for name in archive.namelist() if name.endswith('/boot-release.json'))
        baseline = json.loads(archive.read(baseline_name))
    if baseline != json.loads((ROOT / 'Assets/StreamingAssets/boot-release.json').read_text(encoding='utf-8')):
        failures.append('Source APK baseline differs from final APK')
    if baseline['aotSignature'] != descriptor['aotSignature'] or baseline['dlls'] != descriptor['dlls']:
        failures.append('Clean resource update unexpectedly changed AOT or DLL set')
    if baseline['resourceVersion'] != '3.1.0' or descriptor['resourceVersion'] != '3.1.1':
        failures.append('Unexpected final baseline/update version')
    (EVIDENCE / 'actual-served-release.json').write_bytes(descriptor_bytes)
    summary = {'scenarioCount': len(results), 'failures': failures, 'excludedHistoricalAssertion': ignored,
               'apk': str(apk), 'apkBytes': apk.stat().st_size,
               'apkSha256': hashlib.sha256(apk.read_bytes()).hexdigest(), 'apkBaseline': baseline,
               'actualServedRelease': descriptor, 'httpFiles': served, 'scenarios': results}
    (EVIDENCE / 'final-evidence-index.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'scenarios':len(results),'httpFiles':len(served),'failures':failures,'apkSha256':summary['apkSha256']}))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
