"""Release guard tests, without credentials or any upload calls."""
from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_nexus_upload', ROOT / 'tools/prepare_nexus_upload.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'VERSION').write_text('0.2.5\n', encoding='utf-8')
        (self.root / 'dist').mkdir()
        (self.root / 'dist/MemorialLedger-0.2.5.zip').write_bytes(b'fixture')

    def test_default_dry_run_metadata(self):
        values = prepare.metadata(self.root, 'true', '')
        self.assertEqual(values['version'], '0.2.5')
        self.assertEqual(values['filename'], 'MemorialLedger-0.2.5.zip')
        self.assertEqual(values['sha256'], hashlib.sha256(b'fixture').hexdigest())

    def test_real_upload_requires_exact_confirmation(self):
        for confirmation in ('', '0.2.4', '0.2.5\n', '$(echo 0.2.5)'):
            with self.assertRaises(ValueError):
                prepare.metadata(self.root, 'false', confirmation)
        self.assertEqual(prepare.metadata(self.root, 'false', '0.2.5')['version'], '0.2.5')

    def test_invalid_versions_and_modes_rejected(self):
        with self.assertRaises(ValueError):
            prepare.metadata(self.root, 'yes', '')
        for version in ('../0.2.5', '0.2.5\ninjected=value', 'v0.2.5'):
            (self.root / 'VERSION').write_text(version, encoding='utf-8')
            with self.assertRaises(ValueError):
                prepare.metadata(self.root, 'true', '')

    def test_missing_package_rejected(self):
        (self.root / 'dist/MemorialLedger-0.2.5.zip').unlink()
        with self.assertRaises(FileNotFoundError):
            prepare.metadata(self.root, 'true', '')

    def test_version_tag_selects_real_upload_and_must_match_version(self):
        mode, confirmation = prepare.release_inputs('push', 'refs/tags/v0.2.5', '', '')
        self.assertEqual(mode, 'false')
        self.assertEqual(prepare.metadata(self.root, mode, confirmation)['version'], '0.2.5')
        mode, confirmation = prepare.release_inputs('push', 'refs/tags/v0.2.6', '', '')
        with self.assertRaises(ValueError):
            prepare.metadata(self.root, mode, confirmation)

    def test_ordinary_pushes_and_malformed_tags_rejected(self):
        for ref in ('refs/heads/main', 'refs/tags/vlatest', 'refs/tags/0.2.5',
                    'refs/tags/v0.2.5-beta', 'refs/tags/v0.2.5\ninjected=value'):
            with self.assertRaises(ValueError):
                prepare.release_inputs('push', ref, '', '')

    def test_manual_mode_still_respects_dry_run_and_main(self):
        self.assertEqual(prepare.release_inputs('workflow_dispatch', 'refs/heads/main', 'true', ''), ('true', ''))
        self.assertEqual(prepare.release_inputs('workflow_dispatch', 'refs/heads/main', 'false', '0.2.5'), ('false', '0.2.5'))
        for event, ref in (('workflow_dispatch', 'refs/heads/feature'), ('pull_request', 'refs/heads/main')):
            with self.assertRaises(ValueError):
                prepare.release_inputs(event, ref, 'false', '0.2.5')


if __name__ == '__main__':
    unittest.main()
