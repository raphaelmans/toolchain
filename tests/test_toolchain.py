import unittest
from unittest.mock import patch
from toolchain.__main__ import audit, catalog, make_plan

class ToolchainTest(unittest.TestCase):
    @patch('toolchain.__main__.platform_name', return_value='darwin')
    def test_platform_owner_and_unique_names(self, _):
        tools = catalog()
        self.assertEqual(len({x.name for x in tools}), len(tools))
        self.assertEqual(next(x.owner for x in tools if x.name == 'Git'), 'vendor')
        self.assertFalse(any(x.spec == 'npm:t3' for x in tools))

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

if __name__ == '__main__': unittest.main()
