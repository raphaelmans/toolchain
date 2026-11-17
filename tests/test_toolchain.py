import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from toolchain.__main__ import audit, catalog, make_plan

class ToolchainTest(unittest.TestCase):
    @patch('toolchain.__main__.platform_name', return_value='darwin')
    def test_platform_owner_and_unique_names(self, _):
        tools = catalog()
        self.assertEqual(len({x.name for x in tools}), len(tools))
        self.assertEqual(next(x.owner for x in tools if x.name == 'Git'), 'vendor')
        self.assertFalse(any(x.spec == 'npm:t3' for x in tools))

    @patch('toolchain.__main__.paths', return_value=[])
    def test_opencode_is_vendor_owned_on_every_platform(self, _):
        for platform in ('darwin', 'linux'):
            with self.subTest(platform=platform), patch('toolchain.__main__.platform_name', return_value=platform):
                tool = next(t for t in catalog() if t.name == 'OpenCode')
                self.assertEqual((tool.owner, tool.spec, tool.pin), ('vendor', '', ''))
                self.assertEqual(make_plan([tool])['actions'][0]['command'], [])

    @patch('toolchain.__main__.paths', return_value=[])
    def test_paper_is_vendor_owned_on_every_platform(self, _):
        for platform in ('darwin', 'linux'):
            with self.subTest(platform=platform), patch('toolchain.__main__.platform_name', return_value=platform):
                tool = next(t for t in catalog() if t.name == 'Paper')
                self.assertEqual((tool.owner, tool.command, tool.group), ('vendor', 'paper-desktop', 'Vendor apps'))
                action = make_plan([tool])['actions'][0]
                self.assertEqual(action['command'], [])
                self.assertIn('update-paper.sh', action['note'])
                self.assertIn('https://mcp.paper.design', action['note'])
                self.assertIn('download.paper.design/linux/appImage', action['note'])

    @patch('toolchain.__main__.platform_name', return_value='linux')
    @patch('toolchain.__main__.paths', return_value=[])
    def test_plan_uses_pins_and_leaves_manual_items_manual(self, _, __):
        tools = catalog()
        chosen = [next(t for t in tools if t.name == n) for n in ('Node.js','treg','Git')]
        actions = make_plan(chosen)['actions']
        self.assertEqual(actions[0]['command'], ['mise','use','--global','node@26'])
        self.assertEqual(actions[1]['command'], [])
        self.assertEqual(actions[2]['command'], ['sudo','pacman','-S','--needed','git'])

    @patch('toolchain.__main__.paths', return_value=[])
    def test_audit_schema(self, _):
        data = audit()
        self.assertEqual(data['schema_version'], 1)
        self.assertTrue(all(t['status'] == 'missing' for t in data['tools']))

    def test_npm_executable_discovery_and_planning(self):
        packages = {
            'Playwright CLI': ('playwright-cli', 'npm:@playwright/cli'),
            'Obsidian headless': ('ob', 'npm:obsidian-headless'),
        }
        with TemporaryDirectory() as directory:
            for command, _ in packages.values():
                executable = Path(directory) / command
                executable.write_text('#!/bin/sh\nexit 0\n')
                executable.chmod(0o755)
            for platform in ('darwin', 'linux'):
                with self.subTest(platform=platform), \
                     patch('toolchain.__main__.platform_name', return_value=platform), \
                     patch.dict('os.environ', {'PATH': directory}):
                    rows = {row['name']: row for row in audit()['tools']}
                    selected = [t for t in catalog() if t.name in packages or t.name == 'playwright-cli']
                    actions = {action['name']: action for action in make_plan(selected)['actions']}
                    for name, (command, spec) in packages.items():
                        expected_paths = [str(Path(directory) / command)]
                        self.assertEqual(rows[name]['status'], 'found')
                        self.assertEqual(rows[name]['paths'], expected_paths)
                        self.assertEqual(actions[name]['existing_paths'], expected_paths)
                        self.assertEqual(actions[name]['command'], ['mise', 'use', '--global', f'{spec}@latest'])
                    legacy = rows['playwright-cli']
                    self.assertEqual(legacy['paths'], [])
                    self.assertTrue(legacy['requires_verification'])
                    self.assertEqual((legacy['owner'], legacy['spec'], legacy['pin']), ('mise', 'npm:playwright-cli', 'latest'))
                    self.assertEqual(actions['playwright-cli']['command'], [])
                    self.assertIn('standard', actions['playwright-cli']['note'])

    @patch('toolchain.__main__.platform_name', return_value='linux')
    @patch('toolchain.__main__.paths', return_value=[])
    def test_updater_prerequisites_follow_selection(self, _, __):
        settings = {'Claude Code': 'DISABLE_AUTOUPDATER=1', 'Grok': 'GROK_DISABLE_AUTOUPDATER=1'}
        for names in ((), ('Node.js',), ('Claude Code',), ('Grok',), ('Claude Code', 'Grok')):
            with self.subTest(selected=names):
                plan = make_plan([t for t in catalog() if t.name in names])
                words = ' '.join(plan['prerequisites']).split()
                for name, setting in settings.items():
                    self.assertEqual(setting in words, name in names)
                    if name in names:
                        prerequisite = next(p for p in plan['prerequisites'] if setting in p.split())
                        self.assertIn('Manually persist', prerequisite)
                        self.assertIn(name, prerequisite)
                self.assertEqual(len(plan['actions']), len(names))
                self.assertTrue(all(a['command'][:3] == ['mise', 'use', '--global'] for a in plan['actions']))

    @patch('toolchain.__main__.paths', return_value=[])
    def test_standard_sync_entries(self, _):
        for platform in ('darwin', 'linux'):
            with self.subTest(platform=platform), patch('toolchain.__main__.platform_name', return_value=platform):
                tools = {t.name: t for t in catalog()}
                actions = {a['name']: a for a in make_plan(list(tools.values()))['actions']}
                self.assertEqual(actions['Notion CLI']['command'], ['mise', 'use', '--global', 'npm:ntn@latest'])
                for name, spec in (('treg', 'pipx:tools-registry[proxy]'), ('Defuddle', 'npm:defuddle')):
                    self.assertTrue(tools[name].requires_verification)
                    self.assertEqual((tools[name].owner, tools[name].spec), ('mise', spec))
                    self.assertEqual(actions[name]['command'], [])
                for name in ('lific', 'herdr-viz'):
                    self.assertEqual((tools[name].owner, actions[name]['command']), ('manual', []))

if __name__ == '__main__': unittest.main()
