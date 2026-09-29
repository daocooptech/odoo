# -*- coding: utf-8 -*-
# DAO COOPTECH build of Odoo: what counts as "a call to Odoo S.A. services".
# Shared by strip.py and check.py. See NOTICE.coop.
import ast
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON_DIRS = [os.path.join(ROOT, 'addons'), os.path.join(ROOT, 'odoo', 'addons')]

# Network endpoints of Odoo S.A. services. Links to documentation and to the
# odoo.com website are not calls and are handled by hand (layer B/C).
SERVICE_URL = re.compile(
    r'https?://(?:[a-z0-9-]+\.)*(?:'
    r'api\.odoo\.com|iap[a-z0-9-]*\.odoo\.com|services\.odoo\.com|'
    r'accounts\.odoo\.com|apps\.odoo\.com|partner-autocomplete\.odoo\.com|'
    r'media-api\.odoo\.com|nightly\.odoo\.com|download\.odoo\.com'
    r')', re.I)
SERVICE_IMPORT = re.compile(
    r'(?:odoo\.addons\.|@)(iap|iap_mail|sms|snailmail|partner_autocomplete|'
    r'web_unsplash|google_gmail|microsoft_outlook|base_import_module)\b')

# Modules kept and patched by hand: their calls are removed in the code.
PATCHED = {'base', 'web', 'mail', 'website', 'html_editor', 'digest', 'base_vat'}

# Removed by owner decision, not only for calls. base_vat stays: account
# imports _ref_vat from it; its VIES calls are removed by hand.
EXTRA_SEEDS = set()

SCAN_EXT = ('.py', '.js', '.xml', '.sql', '.csv')
SKIP_PARTS = (os.sep + 'tests' + os.sep, os.sep + 'i18n' + os.sep,
              os.sep + 'static' + os.sep + 'tests' + os.sep,
              os.sep + 'static' + os.sep + 'lib' + os.sep)


def manifests():
    """name -> (path, depends)"""
    found = {}
    for base in ADDON_DIRS:
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            manifest = os.path.join(path, '__manifest__.py')
            if not os.path.isfile(manifest):
                continue
            with open(manifest, encoding='utf-8') as fh:
                data = ast.literal_eval(fh.read())
            found[name] = (path, list(data.get('depends', [])))
    return found


def module_files(path):
    for dirpath, _dirs, files in os.walk(path):
        probe = dirpath + os.sep
        if any(part in probe for part in SKIP_PARTS):
            continue
        for fname in files:
            if fname.endswith(SCAN_EXT) and fname != '__manifest__.py':
                yield os.path.join(dirpath, fname)


def service_hits(path):
    hits = []
    for fpath in module_files(path):
        with open(fpath, encoding='utf-8', errors='ignore') as fh:
            for lineno, line in enumerate(fh, 1):
                if SERVICE_URL.search(line) or SERVICE_IMPORT.search(line):
                    hits.append((fpath, lineno, line.strip()[:160]))
    return hits


def seeds(mods):
    result = set(EXTRA_SEEDS & set(mods))
    for name, (path, _deps) in mods.items():
        if name in PATCHED:
            continue
        if service_hits(path):
            result.add(name)
    return result


def closure(mods, roots):
    removed = set(roots)
    changed = True
    while changed:
        changed = False
        for name, (_path, deps) in mods.items():
            if name not in removed and any(d in removed for d in deps):
                removed.add(name)
                changed = True
    return removed
