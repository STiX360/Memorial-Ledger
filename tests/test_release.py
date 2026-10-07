"""Release guard tests, without credentials or any upload calls."""
from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from release_notes import release_notes
spec = importlib.util.spec_from_file_location('prepare_nexus_upload', ROOT / 'tools/prepare_nexus_upload.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
spec = importlib.util.spec_from_file_location('publish_github_release', ROOT / 'tools/publish_github_release.py')
github = importlib.util.module_from_spec(spec)
spec.loader.exec_module(github)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'VERSION').write_text('0.2.5\n', encoding='utf-8')
        (self.root / 'CHANGELOG.md').write_text(
            '# Changelog\n\n## 0.2.5\n\n- Current changes.\n- Second change.\n\n'
            '## 0.2.4\n\n- Older changes.\n', encoding='utf-8')
        (self.root / 'dist').mkdir()
        (self.root / 'dist/MemorialLedger-0.2.5.zip').write_bytes(b'fixture')

    def test_default_dry_run_metadata(self):
        values = prepare.metadata(self.root, 'true', '')
        self.assertEqual(values['version'], '0.2.5')
        self.assertEqual(values['filename'], 'MemorialLedger-0.2.5.zip')
        self.assertEqual(values['sha256'], hashlib.sha256(b'fixture').hexdigest())
        self.assertEqual(values['changelog'], '- Current changes.\n- Second change.')

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

    def publish(self, run, version='0.2.5', event='push', ref='refs/tags/v0.2.5', checksum=None):
        github.publish(self.root, event, ref, 'STiX360/Memorial-Ledger', version,
                       checksum or hashlib.sha256(b'fixture').hexdigest(), run)

    def test_github_beta_create_attaches_verified_zip(self):
        run = Mock(side_effect=[SimpleNamespace(returncode=1), SimpleNamespace(returncode=0)])
        self.publish(run)
        command = run.call_args.args[0]
        self.assertIn('--prerelease', command)
        self.assertIn('--latest=false', command)
        self.assertIn('--verify-tag', command)
        self.assertIn(str(self.root / 'dist/MemorialLedger-0.2.5.zip'), command)
        self.assertNotIn('--generate-notes', command)
        notes = command[command.index('--notes') + 1]
        self.assertTrue(notes.startswith('- Current changes.\n- Second change.'))
        self.assertNotIn('Older changes', notes)

    def test_github_stable_create_is_not_prerelease(self):
        (self.root / 'VERSION').write_text('1.0.0\n', encoding='utf-8')
        (self.root / 'CHANGELOG.md').write_text('## 1.0.0\n\n- Stable release.\n', encoding='utf-8')
        (self.root / 'dist/MemorialLedger-1.0.0.zip').write_bytes(b'fixture')
        run = Mock(side_effect=[SimpleNamespace(returncode=1), SimpleNamespace(returncode=0)])
        self.publish(run, version='1.0.0', ref='refs/tags/v1.0.0')
        self.assertNotIn('--prerelease', run.call_args.args[0])

    def test_github_guards_fail_before_network(self):
        for kwargs in ({'event': 'workflow_dispatch'}, {'ref': 'refs/heads/main'},
                       {'ref': 'refs/tags/v0.2.6'}, {'checksum': '0' * 64},
                       {'version': '0.2.6', 'ref': 'refs/tags/v0.2.6'},
                       {'version': '../bad'}):
            run = Mock()
            with self.assertRaises(ValueError):
                self.publish(run, **kwargs)
            run.assert_not_called()

    def existing_release(self, assets=(), draft=False, prerelease=True):
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            'assets': [{'name': name} for name in assets], 'isDraft': draft,
            'isPrerelease': prerelease, 'tagName': 'v0.2.5', 'url': 'https://example.test/release'}))

    def test_github_resume_missing_asset_without_clobber(self):
        run = Mock(side_effect=[self.existing_release(draft=True),
                               SimpleNamespace(returncode=0), SimpleNamespace(returncode=0)])
        self.publish(run)
        self.assertEqual(run.call_args_list[1].args[0][1:3], ['release', 'upload'])
        self.assertNotIn('--clobber', run.call_args_list[1].args[0])
        self.assertIn('--draft=false', run.call_args_list[2].args[0])

    def test_github_retry_verifies_existing_asset(self):
        def run(command, **kwargs):
            if command[2] == 'view':
                return self.existing_release(['MemorialLedger-0.2.5.zip'])
            self.assertEqual(command[2], 'download')
            directory = command[command.index('--dir') + 1]
            (Path(directory) / 'MemorialLedger-0.2.5.zip').write_bytes(b'fixture')
            return SimpleNamespace(returncode=0)
        mock = Mock(side_effect=run)
        self.publish(mock)
        self.assertEqual(mock.call_count, 2)

    def test_github_retry_rejects_changed_asset(self):
        def run(command, **kwargs):
            if command[2] == 'view':
                return self.existing_release(['MemorialLedger-0.2.5.zip'])
            directory = command[command.index('--dir') + 1]
            (Path(directory) / 'MemorialLedger-0.2.5.zip').write_bytes(b'changed')
            return SimpleNamespace(returncode=0)
        with self.assertRaisesRegex(ValueError, 'refusing to replace'):
            self.publish(Mock(side_effect=run))

    def test_github_existing_status_requires_manual_review(self):
        run = Mock(return_value=self.existing_release(prerelease=False))
        with self.assertRaises(ValueError):
            self.publish(run)
        self.assertEqual(run.call_count, 1)

    def test_github_command_failure_is_not_swallowed(self):
        import subprocess
        run = Mock(side_effect=[SimpleNamespace(returncode=1),
                               subprocess.CalledProcessError(1, ['gh'])])
        with self.assertRaises(subprocess.CalledProcessError):
            self.publish(run)

    def test_release_workflow_is_independent_and_least_privilege(self):
        import yaml
        workflow = yaml.safe_load((ROOT / '.github/workflows/nexus-upload.yml').read_text(encoding='utf-8'))
        jobs = workflow['jobs']
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        self.assertEqual(jobs['github-release']['permissions'], {'contents': 'write'})
        self.assertEqual(jobs['github-release']['needs'], 'build')
        self.assertEqual(jobs['publish']['needs'], 'build')
        self.assertNotIn('environment', jobs['github-release'])
        self.assertIn("github.event_name == 'push'", jobs['github-release']['if'])
        self.assertIn('!github.event.deleted', jobs['github-release']['if'])
        self.assertEqual(jobs['build']['outputs']['changelog'], '${{ steps.package.outputs.changelog }}')
        upload = next(step for step in jobs['publish']['steps'] if step.get('id') == 'nexus')
        self.assertEqual(upload['with']['changelog'], '${{ needs.build.outputs.changelog }}')
        self.assertEqual(upload['with']['mod_id'], '429496790087')

    def test_notes_missing_empty_or_duplicate_rejected(self):
        for content in ('## 0.2.4\n- Wrong version.\n', '## 0.2.5\n\n',
                        '## 0.2.5\n<!-- TODO -->\n',
                        '## 0.2.5\n- First.\n## 0.2.5\n- Duplicate.\n'):
            (self.root / 'CHANGELOG.md').write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError):
                prepare.metadata(self.root, 'true', '')
            run = Mock()
            with self.assertRaises(ValueError):
                self.publish(run)
            run.assert_not_called()

    def test_notes_stop_at_non_version_heading_and_keep_subsections(self):
        content = ('# Changelog\n## 0.2.5\n- First.\n### Fixes\n- More.\n'
                   '## Upgrade Warning\nNot part of the notes.\n')
        (self.root / 'CHANGELOG.md').write_text(content, encoding='utf-8')
        self.assertEqual(release_notes(self.root, '0.2.5'), '- First.\n### Fixes\n- More.')

    def test_fenced_headings_are_not_release_boundaries(self):
        content = '## 0.2.5\nExample:\n```markdown\n## 0.2.4\n```\n- Fix.\n## 0.2.4\n- Old.\n'
        (self.root / 'CHANGELOG.md').write_text(content, encoding='utf-8')
        self.assertEqual(release_notes(self.root, '0.2.5'),
                         'Example:\n```markdown\n## 0.2.4\n```\n- Fix.')

    def test_multiline_outputs_preserve_notes_without_injected_outputs(self):
        values = prepare.metadata(self.root, 'true', '')
        values['changelog'] += '\nfilename=untrusted\nEOF\nUnicode: \u00e9'
        output = self.root / 'outputs'
        prepare.write_outputs(output, values)
        lines = output.read_text(encoding='utf-8').splitlines()
        decoded = {}
        while lines:
            key, delimiter = lines.pop(0).split('<<', 1)
            body = []
            while lines[0] != delimiter:
                body.append(lines.pop(0))
            lines.pop(0)
            decoded[key] = '\n'.join(body)
        self.assertEqual(decoded, values)


if __name__ == '__main__':
    unittest.main()
