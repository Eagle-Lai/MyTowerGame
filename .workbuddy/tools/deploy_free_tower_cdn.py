#!/usr/bin/env python3
"""Deploy a staged immutable Boot release; activate release.json last.

Generate the source with HotUpdateDeployer.BuildPlan / BootReleaseBuilder.Publish.
Loose bundles and legacy flat paths are deliberately unsupported.
Example, isolated destination:
  python .workbuddy/tools/deploy_free_tower_cdn.py --source Library/FTBootReleaseStage/3.1.0 --destination Builds/BootRefactor/ScriptDeploy
"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path, PurePosixPath


def md5(path):
    digest = hashlib.md5()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(131072), b''):
            digest.update(block)
    return digest.hexdigest()


def contained(root, relative):
    rel = PurePosixPath(relative)
    if not relative or rel.is_absolute() or '..' in rel.parts or '\\' in relative or ':' in relative:
        raise ValueError('Unsafe release path: ' + relative)
    path = root.joinpath(*rel.parts).resolve()
    if root not in path.parents:
        raise ValueError('Release path escapes root: ' + relative)
    return path


def deploy(source, destination):
    source, destination = source.resolve(), destination.resolve()
    pointer = source / 'release.json'
    release = json.loads(pointer.read_text(encoding='utf-8-sig'))
    if release.get('schema') != 2 or release.get('playerApi') != 2:
        raise ValueError('Expected Boot schema 2 / playerApi 2')
    if release.get('contentRoot') != 'releases/' + release['id']:
        raise ValueError('Invalid immutable content root')
    content = contained(source, release['contentRoot'])
    if json.loads((content / 'release.json').read_text(encoding='utf-8-sig')) != release:
        raise ValueError('Root and immutable descriptors differ')
    inventory = json.loads((content / 'payloads.json').read_text(encoding='utf-8-sig'))
    if inventory['version'] != release['resourceVersion']:
        raise ValueError('Inventory resource version mismatch')
    files = []
    for item in inventory['files']:
        path = contained(content, item['path'])
        if not path.is_file() or path.stat().st_size != item['size'] or md5(path) != item['md5']:
            raise ValueError('Payload missing or checksum mismatch: ' + item['path'])
        files.append(path)
    manifest = contained(content, 'FreeTower_' + release['resourceVersion'] + '.bytes')
    if md5(manifest) != release['manifestMd5']:
        raise ValueError('Descriptor manifest checksum mismatch')
    for dll in release['dlls']:
        if md5(contained(content, 'HybridCLR/' + dll['name'])) != dll['md5']:
            raise ValueError('Descriptor DLL checksum mismatch: ' + dll['name'])
    files += [content / 'payloads.json', content / 'release.json']
    pairs = []
    # Resolve destination paths too, rejecting any escaping junctions before activation.
    for src in files:
        target = contained(destination, src.relative_to(source).as_posix())
        if target.exists() and md5(target) != md5(src):
            raise ValueError('Immutable collision: ' + str(target))
        pairs.append((src, target))
    for src, target in pairs:
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.deploying')
        shutil.copyfile(src, temporary)
        if md5(temporary) != md5(src):
            raise ValueError('Copy checksum mismatch: ' + str(src))
        os.replace(temporary, target)
    destination.mkdir(parents=True, exist_ok=True)
    target = contained(destination, 'release.json')
    temporary = target.with_name('release.json.deploying')
    shutil.copyfile(pointer, temporary)
    if md5(temporary) != md5(pointer):
        raise ValueError('Activation descriptor copy checksum mismatch')
    os.replace(temporary, target)
    return {'id': release['id'], 'resourceVersion': release['resourceVersion'],
            'payloadFiles': len(files), 'destination': str(destination), 'activationLast': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(deploy(args.source, args.destination), ensure_ascii=False))


if __name__ == '__main__':
    main()
