import argparse
import curses
import json
import os
import platform
import sys
from dataclasses import asdict
from .catalog import TOOLS


def platform_name():
    return {'Darwin': 'darwin', 'Linux': 'linux'}.get(platform.system(), 'unsupported')

def catalog():
    return [t for t in TOOLS if platform_name() in t.platforms]

def paths(command):
    result = []
    for directory in os.get_exec_path():
        p = os.path.join(directory, command)
        if os.path.isfile(p) and os.access(p, os.X_OK) and p not in result:
            result.append(p)
    return result

def audit():
    rows = []
    for t in catalog():
        found = paths(t.command)
        rows.append({**asdict(t), 'paths': found, 'status': 'found' if found else 'missing'})
    return {'schema_version': 1, 'platform': platform_name(), 'tools': rows,
            'limitations': ['PATH discovery does not establish package ownership or version compliance.', 'Inspect duplicate installations and shell activation before removing anything.']}

def make_plan(selected):
    actions = []
    for t in selected:
        found = paths(t.command)
        note = t.note
        if t.owner == 'mise':
            argv = ['mise', 'use', '--global', f'{t.spec}@{t.pin}']
            if found and not any('/mise/' in p for p in found):
                note += ' Existing executable may have another owner; inspect before migration.'
            if t.name == 'Neovim' and platform_name() == 'linux': note += ' Check Omarchy config compatibility first.'
        elif t.owner == 'brew': argv = ['brew', 'install', t.spec]
        elif t.owner == 'pacman': argv = ['sudo', 'pacman', '-S', '--needed', t.spec]
        else: argv = []
        actions.append({'name': t.name, 'owner': t.owner, 'command': argv, 'existing_paths': found, 'note': note.strip()})
    return {'schema_version': 1, 'platform': platform_name(), 'actions': actions,
            'prerequisites': ['Install the platform package manager and mise 2026.11+ first.', 'Ensure mise is activated in the shell.', 'Review unverified packages and existing owners.'],
            'verification': ['mise doctor', 'mise ls', 'Check command paths and versions in interactive and non-interactive shells.']}

def select(stdscr, items):
    curses.curs_set(0)
    chosen, cursor, top = set(), 0, 0
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        stdscr.addnstr(0, 0, 'Space: toggle  a: all  n: none  g: group  Enter: plan  q: quit', max(0, w-1))
        if cursor < top: top = cursor
        if cursor >= top + max(1, h-2): top = cursor - max(1, h-2) + 1
        for row, i in enumerate(range(top, min(len(items), top + max(1, h-2))), 1):
            t = items[i]
            line = f"[{'x' if i in chosen else ' '}] {t.group} / {t.name} ({t.owner}{' ' + t.pin if t.pin else ''})"
            stdscr.addnstr(row, 0, line, max(0, w-1), curses.A_REVERSE if i == cursor else 0)
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('q'), 27): return None
        if key in (curses.KEY_DOWN, ord('j')): cursor = min(len(items)-1, cursor+1)
        elif key in (curses.KEY_UP, ord('k')): cursor = max(0, cursor-1)
        elif key == ord(' '): chosen.symmetric_difference_update({cursor})
        elif key == ord('a'): chosen = set(range(len(items)))
        elif key == ord('n'): chosen.clear()
        elif key == ord('g'):
            group = {i for i,t in enumerate(items) if t.group == items[cursor].group}
            if group <= chosen: chosen -= group
            else: chosen |= group
        elif key in (10, 13, curses.KEY_ENTER): return [items[i] for i in sorted(chosen)]

def main():
    parser = argparse.ArgumentParser(description='Audit and plan a toolchain migration.')
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('audit', 'catalog', 'select'):
        p = sub.add_parser(name)
        if name != 'select': p.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if platform_name() == 'unsupported': parser.error('Only macOS and Linux are supported.')
    if args.action == 'catalog':
        data = [asdict(t) for t in catalog()]
        if args.json: print(json.dumps(data, indent=2))
        else:
            for t in catalog(): print(f'{t.group:20} {t.name:20} {t.owner:8} {t.spec} {t.pin}')
    elif args.action == 'audit':
        data = audit()
        if args.json: print(json.dumps(data, indent=2))
        else:
            for t in data['tools']: print(f"{t['group']:20} {t['name']:20} {t['owner']:8} {', '.join(t['paths']) or 'missing'}")
            print('\n' + '\n'.join(data['limitations']))
    else:
        if not sys.stdin.isatty() or not sys.stdout.isatty(): parser.error('select requires an interactive terminal')
        selected = curses.wrapper(select, catalog())
        if selected is None: return
        print(json.dumps(make_plan(selected), indent=2))
        print('\nThis is a plan only. Review ownership, prerequisites and commands before running them.')

if __name__ == '__main__': main()
