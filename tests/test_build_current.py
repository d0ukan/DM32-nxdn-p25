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


if __name__ == '__main__':
    unittest.main()
