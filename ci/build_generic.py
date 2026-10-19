"""Unexecuted cloud-only draft. Original synthetic build helper; standard library only."""
import hashlib, json, os, platform, plistlib, shutil, struct, subprocess, zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
NAME = 'GenericGodotIOS'
VERSION = '4.7.2'
ENGINE_COMMIT = 'ed1daf0bf001b61586d9930840f2f1394092c079'
BASE = 'https://github.com/godotengine/godot-builds/releases/download/4.7.2-stable/'
INPUTS = {
    'Godot_v4.7.2-stable_macos.universal.zip': 'c58a24e31d720be9d62f60cb5627c4e695fb72f21b0cfe1bc9ccaa9a3b3ba63e',
    'Godot_v4.7.2-stable_export_templates.tpz': 'f298490b8d44d934be425a5a65a51bf15f422428b229a06a6e11d9ffea248011',
}
IOS_ZIP_SHA = 'fd3280d10dc75356dded006f6f8813f40a5aebd32d128592b781256d8ffbdff4'
MOLTENVK_COMMIT = 'db445ff2042d9ce348c439ad8451112f354b8d2a' # v1.4.1
SPIRV_CROSS_COMMIT = 'adec7acbf41a988713cdb85f93f26c8ca5ea863e'
EXPECTED_FILES = {
    '.github/workflows/build-ios.yml', 'ci/build_generic.py',
    'shell/project.godot', 'shell/main.gd', 'shell/main.tscn', 'shell/export_presets.cfg',
    'README.md', 'LICENSE', 'RELEASE-NOTES.md', 'PUBLIC-FILES.json',
}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

def run(args, capture=False, check=True):
    print('COMMAND', json.dumps([str(x) for x in args]), flush=True)
    return subprocess.run([str(x) for x in args], cwd=ROOT, check=check,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.STDOUT if capture else None)

def download(url, target, expected=None):
    with urlopen(url, timeout=120) as src, target.open('wb') as out:
        shutil.copyfileobj(src, out, 1024 * 1024)
    if expected and sha(target) != expected: raise RuntimeError('Public dependency checksum mismatch')

def check_inputs():
    if os.environ.get('GITHUB_ACTIONS') != 'true': raise RuntimeError('Cloud-only draft: no local execution')
    if os.environ.get('PUBLIC_REPOSITORY_VISIBILITY') != 'public': raise RuntimeError('Public repository required')
    if os.environ.get('GITHUB_RUN_ATTEMPT') != '1': raise RuntimeError('No rerun authorised by this draft')
    if platform.system() != 'Darwin' or platform.machine() != 'arm64': raise RuntimeError('Standard ARM64 Mac required')
    tracked = set(run(['git', 'ls-files', '-z'], True).stdout.decode().split('\0')) - {''}
    if tracked != EXPECTED_FILES: raise RuntimeError('Unexpected tracked inventory')
    manifest = json.loads((ROOT / 'PUBLIC-FILES.json').read_text())
    if set(manifest) != EXPECTED_FILES - {'PUBLIC-FILES.json'}: raise RuntimeError('Unexpected manifest entries')
    for name, expected in manifest.items():
        p = ROOT / name
        if p.is_symlink() or sha(p) != expected: raise RuntimeError('Public input changed: ' + name)
    if shutil.disk_usage(ROOT).free < 5 * 1024**3: raise RuntimeError('Insufficient scratch space')
    xcode = run(['xcodebuild', '-version'], True).stdout.decode()
    if 'Xcode 26.6\n' not in xcode: raise RuntimeError('Expected Xcode26.6 unavailable')
    print(xcode, flush=True)
    return xcode

def inspect_pack(path):
    data = path.read_bytes()
    magic, version, major, minor, patch, flags, filebase, directory = struct.unpack_from('<6I2Q', data)
    if (magic, version, major, minor, patch, flags) != (0x43504447, 4, 4, 7, 2, 2):
        raise RuntimeError('Unexpected placeholder pack header')
    count = struct.unpack_from('<I', data, directory)[0]
    pos = directory + 4
    entries = []
    allowed = {'main.gdc', 'main.gd.remap', 'main.tscn.remap', 'project.binary',
               '.godot/global_script_class_cache.cfg', '.godot/uid_cache.bin'}
    for _ in range(count):
        length = struct.unpack_from('<I', data, pos)[0]; pos += 4
        name = data[pos:pos+length].rstrip(b'\0').decode().removeprefix('res://'); pos += length
        offset, size = struct.unpack_from('<2Q', data, pos); pos += 16
        digest = data[pos:pos+16]; pos += 16
        fflags = struct.unpack_from('<I', data, pos)[0]; pos += 4
        payload = data[filebase+offset:filebase+offset+size]
        exported_main = name.startswith('.godot/exported/') and name.endswith('-main.scn')
        if (name not in allowed and not exported_main) or fflags or len(payload) != size or hashlib.md5(payload).digest() != digest:
            raise RuntimeError('Unexpected placeholder pack entry: ' + name)
        entries.append({'path': name, 'bytes': size, 'sha256': hashlib.sha256(payload).hexdigest()})
    if 'project.binary' not in {e['path'] for e in entries}: raise RuntimeError('Missing project settings')
    return entries

def main():
    xcode = check_inputs()
    work = ROOT / '.scratch'; work.mkdir(exist_ok=False)
    output = ROOT / 'release'; output.mkdir(exist_ok=False)
    for name, digest in INPUTS.items(): download(BASE + name, work / name, digest)
    editor_dir = work / 'editor'; editor_dir.mkdir()
    run(['/usr/bin/unzip', '-q', work / 'Godot_v4.7.2-stable_macos.universal.zip', '-d', editor_dir])
    editor = editor_dir / 'Godot.app/Contents/MacOS/Godot'
    editor.chmod(0o755)
    engine = run([editor, '--version'], True).stdout.decode().strip()
    if engine != '4.7.2.stable.official.ed1daf0bf': raise RuntimeError('Editor version mismatch')
    template_dir = Path.home() / 'Library/Application Support/Godot/export_templates/4.7.2.stable'
    template_dir.mkdir(parents=True, exist_ok=True)
    ios_zip = template_dir / 'ios.zip'
    with zipfile.ZipFile(work / 'Godot_v4.7.2-stable_export_templates.tpz') as z:
        with z.open('templates/ios.zip') as src, ios_zip.open('wb') as dst: shutil.copyfileobj(src, dst)
    if sha(ios_zip) != IOS_ZIP_SHA: raise RuntimeError('iOS template mismatch')
    target = work / 'xcode'; target.mkdir()
    run([editor, '--headless', '--path', ROOT / 'shell', '--editor', '--import'])
    run([editor, '--headless', '--path', ROOT / 'shell', '--export-release', 'Generic iOS Shell', target / (NAME + '.ipa')])
    project = target / (NAME + '.xcodeproj')
    if not project.is_dir(): raise RuntimeError('Expected generated project missing')
    project_info = run(['xcodebuild', '-list', '-json', '-project', project], True).stdout.decode()
    if NAME not in json.loads(project_info)['project']['schemes']: raise RuntimeError('Expected scheme missing')
    derived = work / 'derived'
    run(['xcodebuild', '-project', project, '-scheme', NAME, '-configuration', 'Release',
         '-sdk', 'iphoneos', '-destination', 'generic/platform=iOS', '-derivedDataPath', derived,
         'ARCHS=arm64', 'ONLY_ACTIVE_ARCH=NO', 'CODE_SIGNING_ALLOWED=NO',
         'CODE_SIGNING_REQUIRED=NO', 'CODE_SIGN_IDENTITY=', 'build'])
    app = derived / 'Build/Products/Release-iphoneos' / (NAME + '.app')
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    if info.get('CFBundleExecutable') != NAME or info.get('CFBundleIdentifier') != 'org.example.genericgodot.iosshell':
        raise RuntimeError('Unexpected native bundle metadata')
    if info.get('CFBundleSupportedPlatforms') != ['iPhoneOS']: raise RuntimeError('Not a device bundle')
    executable = app / NAME
    binary = executable.read_bytes()
    magic, cpu, _, filetype, ncmds, _, _, _ = struct.unpack_from('<8I', binary)
    if (magic, cpu, filetype) != (0xFEEDFACF, 0x100000C, 2): raise RuntimeError('Not an ARM64 Mach-O executable')
    pos = 32; build_platforms = []
    for _ in range(ncmds):
        cmd, size = struct.unpack_from('<2I', binary, pos)
        if size < 8: raise RuntimeError('Invalid load command')
        if cmd == 0x32: build_platforms.append(struct.unpack_from('<I', binary, pos + 8)[0])
        pos += size
    if build_platforms != [2]: raise RuntimeError('Not an iOS-device executable')
    arch = run(['lipo', '-archs', executable], True).stdout.decode().strip()
    if arch != 'arm64': raise RuntimeError('Unexpected architecture')
    for forbidden in ['embedded.mobileprovision', '_CodeSignature']:
        if list(app.rglob(forbidden)): raise RuntimeError('Unexpected signing/provisioning material')
    if run(['codesign', '-d', executable], True, False).returncode == 0:
        raise RuntimeError('App signature present; stop, do not strip or re-sign automatically')
    upstream_framework_signatures = {}
    for candidate in (app / 'Frameworks').glob('*.framework'):
        upstream_framework_signatures[candidate.name] = run(['codesign', '-d', candidate], True, False).returncode == 0
    packs = list(app.rglob('*.pck'))
    if packs != [app / (NAME + '.pck')]: raise RuntimeError('Unexpected main-pack slot')
    pack_entries = inspect_pack(packs[0])
    notices = app / 'Notices/Godot'; notices.mkdir(parents=True)
    for name in ['LICENSE.txt', 'COPYRIGHT.txt', 'AUTHORS.md']:
        download('https://raw.githubusercontent.com/godotengine/godot/' + ENGINE_COMMIT + '/' + name, notices / name)
    for component, revision in [('MoltenVK', MOLTENVK_COMMIT), ('SPIRV-Cross', SPIRV_CROSS_COMMIT)]:
        directory = app / 'Notices' / component; directory.mkdir()
        for name in ['LICENSE', 'README.md']:
            download('https://raw.githubusercontent.com/KhronosGroup/' + component + '/' + revision + '/' + name, directory / name)
    shutil.copy2(ROOT / 'LICENSE', app / 'Notices/Synthetic-LICENSE.txt')
    files = {str(p.relative_to(app)): {'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(app.rglob('*')) if p.is_file()}
    metadata = {'engine_input_version': engine, 'engine_commit': ENGINE_COMMIT,
                'engine_version_not_executed_on_ios': True, 'configuration': 'Release',
                'architecture': arch, 'macho_platform': 'iOS device', 'signed': False,
                'xcode': xcode.strip(), 'ios_template_sha256': IOS_ZIP_SHA,
                'preexisting_framework_signatures_detected': upstream_framework_signatures,
                'notice_sources': {'Godot': ENGINE_COMMIT, 'MoltenVK': MOLTENVK_COMMIT, 'SPIRV-Cross': SPIRV_CROSS_COMMIT},
                'official_download_checksums': INPUTS, 'bundle_id': info['CFBundleIdentifier'],
                'pck_slot': NAME + '.pck', 'placeholder_pck_entries': pack_entries,
                'source_commit': os.environ['GITHUB_SHA'], 'run_id': os.environ['GITHUB_RUN_ID'],
                'runtime_and_device_testing': 'UNVERIFIED', 'bundle_files': files}
    (output / 'BUILD-INFO.json').write_text(json.dumps(metadata, indent=2) + '\n')
    package = output / (NAME + '-unsigned.zip')
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(app.rglob('*')):
            if p.is_file(): z.write(p, 'Payload/' + NAME + '.app/' + str(p.relative_to(app)))
    if package.stat().st_size >= 2 * 1024**3: raise RuntimeError('Release asset exceeds documented limit')
    (output / 'SHA256SUMS').write_text(''.join(sha(output / n) + '  ' + n + '\n' for n in [package.name, 'BUILD-INFO.json']))
    print('READY_FOR_SEPARATELY_AUTHORISED_PUBLIC_RELEASE', package.name, package.stat().st_size, sha(package))

if __name__ == '__main__':
    main()
