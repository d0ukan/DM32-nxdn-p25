import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('build_current', Path(__file__).parents[1] / 'tools/build_current.py')
build_current = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_current)


class BuildTreeGuards(unittest.TestCase):
    def test_refuses_nonempty_directory_without_initializing_git(self):
        with TemporaryDirectory() as directory:
            tree = Path(directory)
            existing = tree / 'backup.txt'
            existing.write_text('keep this file', encoding='utf-8')
            with patch.object(build_current, 'run') as run:
                run.side_effect = AssertionError('Git ran in a nonempty directory')
                with self.assertRaisesRegex(SystemExit, 'not empty'):
                    build_current.prepare(tree)
                run.assert_not_called()
            self.assertEqual(existing.read_text(encoding='utf-8'), 'keep this file')
            self.assertFalse((tree / '.git').exists())

    def test_refuses_linked_checkout(self):
        with TemporaryDirectory() as directory:
            tree = Path(directory)
            (tree / '.git').write_text('gitdir: another-checkout\n', encoding='utf-8')
            with patch.object(build_current, 'run') as run, patch.object(build_current, 'out') as out:
                with self.assertRaisesRegex(SystemExit, 'linked checkout'):
                    build_current.prepare(tree)
                run.assert_not_called()
                out.assert_not_called()

    def test_refuses_branch_at_the_build_pin(self):
        with TemporaryDirectory() as directory:
            tree = Path(directory)
            (tree / '.git').mkdir()
            with patch.object(build_current, 'run') as run, patch.object(
                build_current, 'out', side_effect=[build_current.PIN, 'main']
            ):
                with self.assertRaisesRegex(SystemExit, 'checked-out branch'):
                    build_current.prepare(tree)
                run.assert_not_called()

    def test_allows_reusing_a_detached_build_tree(self):
        with TemporaryDirectory() as directory:
            tree = Path(directory)
            (tree / '.git').mkdir()
            with patch.object(build_current, 'run') as run, patch.object(
                build_current, 'out', side_effect=[build_current.PIN, 'HEAD']
            ), patch.object(build_current, 'PATCHES', ()):
                build_current.prepare(tree)
                run.assert_any_call('git', 'submodule', 'update', '--init', '--depth=1',
                                    'third_party/FreeRTOS-Kernel', cwd=tree)


if __name__ == '__main__':
    unittest.main()
