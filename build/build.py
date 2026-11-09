#!/usr/bin/env python3
"""Rebuild the link-qc plugin from the AhmedZaher1233/Link_AI_Pro skills.

    python build/build.py --upstream <Link_AI_Pro checkout> [--sha <commit>]
    python build/build.py --package dist/link-qc.plugin

What a build does:
  1. copies every skill folder from <upstream>/.claude/skills (minus EXCLUDE)
     plus build/extra-skills/* (our own skills, e.g. ado-bug-report);
  2. rewrites `.claude/skills/` to `<plugin-root>/skills/` in .md/.txt files
     and adds a one-line note explaining <plugin-root> to those skills;
  3. makes every description plugin-valid (<= 1024 chars, no <tags>,
     valid YAML), using build/descriptions.yaml overrides first, else an
     automatic short version; the full original text moves into the body;
  4. applies the "plugin mode" patches to skill 1 (see SKILL1_PATCHES);
  5. validates the result, and only if it differs from skills/ replaces
     skills/, bumps the patch version and writes build/state.json.

It never writes anything when a step fails (exit code 1), so a changed
upstream can never ship a half-fixed plugin.
"""
import argparse, hashlib, json, os, re, shutil, sys, tempfile, textwrap, zipfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'build')
EXCLUDE = {'find-skills'}            # upstream skills we do not ship
TEXT_EXT = ('.md', '.txt')           # only docs are path-rewritten, never code
MAX_DESC = 1024
NOTE = ('> **Script paths:** `<plugin-root>` is the folder this plugin is installed in, two levels '
        "above this skill's base directory (`<base-dir>/../..`). If this skill was copied into a "
        "project instead, `<plugin-root>` is that project's `.claude` folder.")
SKILL1 = 'link-qc-1-generate-update-testing-structure'
SKILL1_SCRIPTS = '.claude/skills/' + SKILL1 + '/scripts/'
N = '\n'
SKILL1_PATCHES = [  # (file, old, new) - exact text; a missing `old` fails the build
    ('scripts/lib.mjs', "import { execSync } from 'node:child_process';",
     "import { execSync } from 'node:child_process';" + N + "import { fileURLToPath } from 'node:url';"),
    ('scripts/lib.mjs', "  const dirName = actualName(claude, 'skills');",
     "  // Plugin mode: this file sits at <plugin-root>/skills/<skill-1>/scripts/lib.mjs" + N +
     "  const pluginRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');" + N +
     "  const fromPlugin = !process.env.LINK_QC_PROJECT_MODE && isFile(path.join(pluginRoot, '.claude-plugin', 'plugin.json'));" + N +
     "  const dirName = fromPlugin ? 'skills' : actualName(claude, 'skills');"),
    ('scripts/lib.mjs', "  const skillsDir = dirName ? path.join(claude, dirName) : null;",
     "  const skillsDir = fromPlugin ? path.join(pluginRoot, 'skills') : (dirName ? path.join(claude, dirName) : null);"),
    ('scripts/lib.mjs', "    uppercaseDir: dirName !== null && dirName !== 'skills',",
     "    source: fromPlugin ? 'plugin' : 'project'," + N + "    uppercaseDir: dirName !== null && dirName !== 'skills',"),
    ('scripts/validate-setup.mjs',
     "row('sync-skills cmd', isFile(path.join(root, SYNC_COMMAND)) ? 'PASS' : 'FAIL', SYNC_COMMAND);",
     "row('sync-skills cmd', su.source === 'plugin' || isFile(path.join(root, SYNC_COMMAND)) ? 'PASS' : 'FAIL', "
     "su.source === 'plugin' ? 'not needed: skills come from the link-qc plugin' : SYNC_COMMAND);"),
    ('SKILL.md', '| 3 | **Skills sync** — Mode A:',
     '| 3 | **Skills sync** — **Plugin mode** (preflight `suite.source` is `plugin`): skip this step entirely '
     'and never run `sync-qa-skills.mjs`; the skills update when the plugin is updated, and optional tools go '
     'through `references/toolchain.md`. Otherwise — Mode A:'),
    ('SKILL.md', '   is `.claude/skills/` (lowercase).',
     '   is `.claude/skills/` (lowercase).' + N + '   **Plugin mode:** when this skill runs from the installed '
     'link-qc plugin, the plugin IS the skills source. Never download skills into the project.'),
]


def fail(msg):
    print('BUILD FAILED: ' + msg, file=sys.stderr)
    sys.exit(1)


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)


FM = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n', re.S)
DESC = re.compile(r'^description:.*?(?=^[A-Za-z][\w-]*:|\Z)', re.S | re.M)


def frontmatter(text, where):
    m = FM.match(text)
    if not m:
        fail(f'{where}: SKILL.md has no frontmatter')
    return m


def raw_description(fm):
    try:
        data = yaml.safe_load(fm)
        if isinstance(data, dict) and isinstance(data.get('description'), str):
            return data['description'], True
    except yaml.YAMLError:
        pass
    m = DESC.search(fm)
    if not m:
        return '', False
    body = m.group(0)[len('description:'):].strip()
    body = re.sub(r'^[>|][-+]?\s*', '', body)
    return re.sub(r'\s+', ' ', body).strip().strip('"\''), False


def detag(s):
    return re.sub(r'<([^<>]*)>', r'{\1}', s)


def shorten(desc, limit=1000):
    """Head of the description cut at a sentence end, plus its trigger phrases."""
    desc = re.sub(r'\s+', ' ', desc).strip()
    ms = list(re.finditer(r'(?i)\btrigger(?:s|ed)? on\b|\btrigger on phrases like\b', desc))
    m = ms[0] if ms else re.search(r'(?i)\buse (?:it )?(?:when|for)\b', desc)
    trig_src = desc[m.start():] if m else ''
    phrases = re.findall(r'"([^"]{2,80})"|“([^”]{2,80})”', trig_src)
    phrases = [a or b for a, b in phrases if len(a or b) > 3]
    trig = ''
    for ph in phrases:
        nxt = (trig + ', ' if trig else 'Trigger on ') + f'"{ph}"'
        if len(nxt) > 380:
            break
        trig = nxt
    trig = trig + '.' if trig else ''
    budget = limit - len(trig) - 1
    head = desc[:m.start()].strip() if m and m.start() > 120 else desc
    if len(head) > budget:
        cut = head[:budget]
        end = max(cut.rfind('. '), cut.rfind('; '))
        head = cut[:end + 1] if end > budget // 2 else cut[:cut.rfind(' ')].rstrip(',;:—-') + '…'
    out = (head + ' ' + trig).strip()
    return out[:limit]


def fix_description(path, name, overrides, report):
    text = read(path)
    m = frontmatter(text, name)
    fm, body = m.group(1), text[m.end():]
    desc, yaml_ok = raw_description(fm)
    if not desc:
        fail(f'{name}: no description')
    if name in overrides:
        new, why = overrides[name].strip(), 'override'
    elif yaml_ok and len(desc) <= MAX_DESC and not re.search(r'<[^<>]*>', desc):
        return
    elif len(detag(desc)) <= MAX_DESC:
        new, why = detag(desc), 'fixed tags/YAML'
    else:
        new, why = shorten(detag(desc)), f'auto-shortened from {len(desc)}'
    new = re.sub(r'\s+', ' ', new).strip()
    if len(new) > MAX_DESC or re.search(r'<[^<>]*>', new):
        fail(f'{name}: description still invalid after fix ({len(new)} chars)')
    span = DESC.search(fm)
    block = 'description: >\n' + '\n'.join('  ' + line for line in textwrap.wrap(new, 96, break_on_hyphens=False, break_long_words=False)) + '\n'
    fm2 = (fm[:span.start()] + block + fm[span.end():]).rstrip('\n')
    if why.startswith('auto') or why == 'override':
        body = '\n## Full scope (moved from the description)\n\n' + desc.strip() + '\n' + body
    write(path, '---\n' + fm2 + '\n---\n' + body)
    report.append(f'  description {name}: {why}')


def rewrite_paths(skill_dir, name):
    touched = False
    for dp, _, files in os.walk(skill_dir):
        for fn in files:
            p = os.path.join(dp, fn)
            if name == SKILL1:
                if not fn.endswith(TEXT_EXT + ('.ps1', '.sh')):
                    continue
                old, new = SKILL1_SCRIPTS, SKILL1_SCRIPTS.replace('.claude/', '<plugin-root>/')
            else:
                if not fn.endswith(TEXT_EXT):
                    continue
                old, new = '.claude/skills/', '<plugin-root>/skills/'
            t = read(p)
            if old in t:
                write(p, t.replace(old, new))
                touched = True
    return touched


def add_note(skill_md):
    t = read(skill_md)
    if 'Script paths:** `<plugin-root>`' in t:
        return
    m = frontmatter(t, skill_md)
    write(skill_md, t[:m.end()] + '\n' + NOTE + '\n' + t[m.end():])


def patch_skill1(stage):
    base = os.path.join(stage, SKILL1)
    if not os.path.isdir(base):
        fail(f'{SKILL1} missing upstream')
    for rel, old, new in SKILL1_PATCHES:
        p = os.path.join(base, rel)
        t = read(p)
        if new in t:
            continue
        if t.count(old) != 1:
            fail(f'{SKILL1}/{rel}: plugin-mode patch no longer applies (text changed upstream): {old[:60]}')
        write(p, t.replace(old, new))
    # the self-test builds fixture projects, so it must scan them, not the plugin
    p = os.path.join(base, 'scripts', 'selftest.mjs')
    t = read(p)
    flag = "process.env.LINK_QC_PROJECT_MODE = '1'; // plugin build: self-test scans its fixtures"
    if flag not in t:
        imports = [m for m in re.finditer(r'^import .*?;[ \t]*$', t, re.M)]
        if not imports:
            fail(f'{SKILL1}/scripts/selftest.mjs: no import lines to anchor the project-mode flag')
        end = imports[-1].end()
        write(p, t[:end] + '\n' + flag + t[end:])


def validate(stage):
    names = []
    for name in sorted(os.listdir(stage)):
        p = os.path.join(stage, name, 'SKILL.md')
        t = read(p)
        data = yaml.safe_load(frontmatter(t, name).group(1))
        d = data.get('description', '')
        if data.get('name') != name:
            fail(f'{name}: frontmatter name is {data.get("name")!r}')
        if not d or len(d) > MAX_DESC or re.search(r'<[^<>]*>', d):
            fail(f'{name}: invalid description ({len(d)} chars)')
        names.append(name)
    return names


def tree_hash(d):
    h = hashlib.sha256()
    for dp, dn, files in os.walk(d):
        dn.sort()
        for fn in sorted(files):
            p = os.path.join(dp, fn)
            h.update(os.path.relpath(p, d).replace(os.sep, '/').encode())
            with open(p, 'rb') as f:
                h.update(f.read())
    return h.hexdigest()


def bump(version):
    major, minor, patch = (int(x) for x in version.split('.'))
    return f'{major}.{minor}.{patch + 1}'


def package(out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for top in ('.claude-plugin', 'skills'):
            for dp, dn, files in os.walk(os.path.join(ROOT, top)):
                dn[:] = [x for x in dn if x not in ('node_modules', '__pycache__')]
                for fn in files:
                    p = os.path.join(dp, fn)
                    z.write(p, os.path.relpath(p, ROOT).replace(os.sep, '/'))
    print(f'packaged {out}')


def gh_output(**kv):
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a') as f:
            for k, v in kv.items():
                f.write(f'{k}={v}\n')


def build(upstream, sha):
    src = os.path.join(upstream, '.claude', 'skills')
    if not os.path.isdir(src):
        fail(f'no .claude/skills in {upstream}')
    ov_path = os.path.join(BUILD, 'descriptions.yaml')
    overrides = (yaml.safe_load(read(ov_path)) or {}) if os.path.exists(ov_path) else {}
    tmp = tempfile.mkdtemp()
    stage = os.path.join(tmp, 'skills')
    os.makedirs(stage)
    report = []
    for name in sorted(os.listdir(src)):
        if name in EXCLUDE or not os.path.isfile(os.path.join(src, name, 'SKILL.md')):
            continue
        shutil.copytree(os.path.join(src, name), os.path.join(stage, name))
    extra = os.path.join(BUILD, 'extra-skills')
    for name in sorted(os.listdir(extra)) if os.path.isdir(extra) else []:
        if os.path.exists(os.path.join(stage, name)):
            report.append(f'  note: {name} now exists upstream; using our extra-skills copy')
            shutil.rmtree(os.path.join(stage, name))
        shutil.copytree(os.path.join(extra, name), os.path.join(stage, name))
    patch_skill1(stage)
    for name in sorted(os.listdir(stage)):
        d = os.path.join(stage, name)
        if rewrite_paths(d, name):
            add_note(os.path.join(d, 'SKILL.md'))
        fix_description(os.path.join(d, 'SKILL.md'), name, overrides, report)
    names = validate(stage)

    new_hash = tree_hash(stage)
    state_p = os.path.join(BUILD, 'state.json')
    state = json.loads(read(state_p)) if os.path.exists(state_p) else {}
    manifest_p = os.path.join(ROOT, '.claude-plugin', 'plugin.json')
    manifest = json.loads(read(manifest_p))
    print(f'{len(names)} skills: ' + ', '.join(names))
    print('\n'.join(report))
    if state.get('hash') == new_hash and os.path.isdir(os.path.join(ROOT, 'skills')):
        print(f'no change (still v{manifest["version"]})')
        gh_output(changed='false', version=manifest['version'])
        return
    dest = os.path.join(ROOT, 'skills')
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(stage, dest)
    if state.get('hash'):
        manifest['version'] = bump(manifest['version'])
    write(manifest_p, json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    write(state_p, json.dumps({'upstream': 'AhmedZaher1233/Link_AI_Pro', 'upstreamSha': sha,
                               'hash': new_hash, 'version': manifest['version'],
                               'skills': names}, indent=2) + '\n')
    print(f'CHANGED -> v{manifest["version"]}')
    gh_output(changed='true', version=manifest['version'])
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--upstream')
    ap.add_argument('--sha', default='unknown')
    ap.add_argument('--package')
    a = ap.parse_args()
    if a.package:
        package(a.package)
    elif a.upstream:
        build(a.upstream, a.sha)
    else:
        ap.error('give --upstream or --package')
