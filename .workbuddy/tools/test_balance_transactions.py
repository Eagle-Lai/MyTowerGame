#!/usr/bin/env python3
"""Fault-injection checks of the actual transaction core; all writes use temporary roots."""
from __future__ import annotations
import argparse
import contextlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
from unittest import mock

REAL_ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('balance_pipeline_fault_test_subject', pathlib.Path(__file__).with_name('balance_pipeline.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class TransactionFaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='FTProject-balance-transactions-')
        self.root = pathlib.Path(self.temp.name)
        self.data = self.root / 'Luban/Config/Datas'
        self.jobs = self.root / 'Library/BalanceWorkbench'
        self.design = self.root / 'Luban/BalanceDesign'
        self.data.mkdir(parents=True); self.jobs.mkdir(parents=True); self.design.mkdir(parents=True)
        self.original_globals = {name: getattr(core, name) for name in ['ROOT', 'DATA', 'JOBS', 'DESIGN', 'DEFAULT_RECIPE', 'MANIFEST', 'STATE']}
        core.ROOT = self.root; core.DATA = self.data; core.JOBS = self.jobs; core.DESIGN = self.design
        core.DEFAULT_RECIPE = self.design / 'balance_design.json'; core.MANIFEST = self.design / 'variant_manifest.json'; core.STATE = self.design / 'applied_state.json'
        self.formal = self.root / 'Assets/ConfigJson'
        self.formal.mkdir(parents=True)
        (self.formal / 'stable.json').write_text('ORIGINAL FORMAL CONTENT', encoding='utf-8')

    def tearDown(self):
        for name, value in self.original_globals.items(): setattr(core, name, value)
        self.temp.cleanup()

    def files(self):
        stage = self.jobs / 'job' / 'stage'; stage.mkdir(parents=True)
        (stage / 'a').write_bytes(b'new a'); (stage / 'b').write_bytes(b'new b'); (stage / 'c').write_bytes(b'new c')
        (self.formal / 'a').write_bytes(b'old a'); (self.formal / 'b').write_bytes(b'old b')
        return [(stage / name, self.formal / name) for name in ['a', 'c', 'b']]

    def formal_hashes(self):
        return {str(p.relative_to(self.root)): core.file_hash(p) for parent in [self.formal, self.root / 'Assets/Gen', self.data, self.design] for p in parent.rglob('*') if p.is_file()}

    def minimal_plan(self):
        return {'profileId': 'D04', 'sourceHashes': {'Assets/ConfigJson/stable.json': core.file_hash(self.formal / 'stable.json')}, 'tables': {'tblevelrating': []}, 'recipe': {}, 'manifest': {}}

    def stage_excel_fixture(self, stage, plan):
        stage.mkdir(parents=True, exist_ok=True)
        (stage / 'unchanged-source.xlsx').write_bytes(b'staged only; formal untouched')

    def stage_complete_excel_fixture(self, stage, plan):
        stage.mkdir(parents=True, exist_ok=True)
        for name in list(core.TABLE_FILES.values()) + ['__tables__', 'Localization']:
            (stage / (name + '.xlsx')).write_bytes(('isolated staged workbook ' + name).encode())

    def stage_luban_fixture(self, data, gen, config, cache):
        gen.mkdir(parents=True, exist_ok=True); config.mkdir(parents=True, exist_ok=True)
        (gen / 'test.cs').write_text('// isolated generated fixture', encoding='utf-8')
        (config / 'stable.json').write_text('STAGED CANDIDATE', encoding='utf-8')

    def test_commit_interruption_rolls_back_written_and_new_files(self):
        files = self.files(); before = self.formal_hashes(); real_replace = core.os.replace
        def interrupt(src, dst):
            if pathlib.Path(dst).name == 'b': raise OSError('injected interrupted application after two committed files')
            return real_replace(src, dst)
        with mock.patch.object(core.os, 'replace', side_effect=interrupt):
            with self.assertRaisesRegex(OSError, 'injected interrupted'): core.commit_files(files, self.jobs / 'job', {'profileId': 'D04'})
        self.assertEqual(before, self.formal_hashes())
        self.assertEqual('rolled_back', core.read_json(self.jobs / 'job/transaction.json')['phase'])
        self.assertFalse((self.formal / 'c').exists())

    def test_restore_committed_transaction_and_repeat_is_idempotent(self):
        files = self.files(); before = self.formal_hashes()
        journal = core.commit_files(files, self.jobs / 'job', {'profileId': 'D04'})
        self.assertEqual('committed', journal['phase']); self.assertNotEqual(before, self.formal_hashes())
        core.restore_transaction(journal); self.assertEqual(before, self.formal_hashes())
        core.restore_transaction(journal); self.assertEqual(before, self.formal_hashes())

    def test_restore_mapped_destination_stages_before_atomic_replace(self):
        files = self.files(); before = self.formal_hashes()
        journal = core.commit_files(files, self.jobs / 'job', {'profileId': 'D04'})
        real_copy = core.shutil.copy2
        destinations = []
        def mapped_copy(src, dst, *args, **kwargs):
            destination = pathlib.Path(dst)
            if destination in [pair[1] for pair in files]:
                raise OSError(1224, 'destination has a live mapped view')
            destinations.append(destination)
            return real_copy(src, dst, *args, **kwargs)
        with mock.patch.object(core.shutil, 'copy2', side_effect=mapped_copy):
            core.restore_transaction(journal)
            core.restore_transaction(journal)
        self.assertEqual(before, self.formal_hashes())
        self.assertEqual(2, len(destinations))
        self.assertTrue(all('.rollback-' in p.name for p in destinations))
        self.assertFalse(list(self.formal.glob('*.rollback-*.tmp')))

    def test_restore_staging_failure_preserves_mapped_destination_and_cleans_temp(self):
        files = self.files()
        journal = core.commit_files(files, self.jobs / 'job', {'profileId': 'D04'})
        after = self.formal_hashes()
        def partial_copy(src, dst):
            pathlib.Path(dst).write_bytes(b'incomplete backup copy')
            raise OSError('injected backup staging failure')
        with mock.patch.object(core.shutil, 'copy2', side_effect=partial_copy):
            with self.assertRaisesRegex(OSError, 'backup staging failure'):
                core.restore_transaction(journal)
        self.assertEqual(after, self.formal_hashes())
        self.assertFalse(list(self.formal.glob('*.rollback-*.tmp')))

    def test_public_rollback_rejects_external_changes_without_touching_other_files(self):
        files = self.files(); core.commit_files(files, self.jobs / 'job', {'profileId': 'D04'})
        (self.formal / 'a').write_bytes(b'another task edited this after apply')
        protected = self.formal_hashes()
        with self.assertRaisesRegex(RuntimeError, 'External modifications block rollback'): core.rollback(self.jobs / 'job')
        self.assertEqual(protected, self.formal_hashes()); self.assertFalse((self.jobs / 'apply.lock').exists())

    def test_active_lock_refuses_second_owner_and_releases_on_exception(self):
        with self.assertRaisesRegex(ValueError, 'owner fails'):
            with core.job_lock():
                self.assertEqual(str(os.getpid()), (self.jobs / 'apply.lock').read_text())
                with self.assertRaisesRegex(RuntimeError, 'active application|acquired'):
                    with core.job_lock(): self.fail('a second owner entered the protected section')
                raise ValueError('owner fails')
        self.assertFalse((self.jobs / 'apply.lock').exists())

    def test_exited_owner_recovers_incomplete_journal_before_next_apply(self):
        files = self.files(); before = self.formal_hashes()
        journal = core.commit_files(files, self.jobs / 'job', {'profileId': 'D04'})
        journal['phase'] = 'committing'; core.write_json(self.jobs / 'job/transaction.json', journal)
        exited = subprocess.Popen([sys.executable, '-c', 'pass']); exited.wait(timeout=10)
        (self.jobs / 'apply.lock').write_text(str(exited.pid))
        with core.job_lock(): self.assertEqual(before, self.formal_hashes())
        self.assertEqual('rolled_back', core.read_json(self.jobs / 'job/transaction.json')['phase'])

    def test_blocked_recovery_is_retried_even_after_lock_removed(self):
        files = self.files(); before = self.formal_hashes()
        journal = core.commit_files(files, self.jobs / 'job', {'profileId': 'D04'})
        journal['phase'] = 'rollback_blocked'; core.write_json(self.jobs / 'job/transaction.json', journal)
        (self.formal / 'a').write_bytes(b'external edit blocks safe recovery')
        protected = self.formal_hashes()
        for attempt in range(2):
            with self.assertRaisesRegex(RuntimeError, 'External modifications block rollback'):
                with core.job_lock(): self.fail('incomplete recovery was bypassed on attempt ' + str(attempt))
            self.assertEqual(protected, self.formal_hashes()); self.assertFalse((self.jobs / 'apply.lock').exists())
        (self.formal / 'a').write_bytes(b'new a')
        with core.job_lock(): self.assertEqual(before, self.formal_hashes())
        self.assertEqual('rolled_back', core.read_json(self.jobs / 'job/transaction.json')['phase'])

    def test_final_readback_failure_rolls_back_entire_committed_transaction(self):
        plan = self.minimal_plan(); before = self.formal_hashes(); out = self.jobs / 'readback-failure'
        def validate(candidate, exported=None):
            if exported == self.formal: return {'passed': False, 'errors': ['injected final readback mismatch']}
            return {'passed': True, 'errors': []}
        with mock.patch.object(core, 'validate', side_effect=validate), mock.patch.object(core, 'excel_write', side_effect=self.stage_complete_excel_fixture), mock.patch.object(core, 'luban_export', side_effect=self.stage_luban_fixture), mock.patch.object(core, 'runtime_content_hash', return_value='fixture-content-hash'), mock.patch.object(core, 'write_rating_excel'):
            with self.assertRaisesRegex(RuntimeError, 'Final readback failed; transaction restored'): core.apply_plan(plan, out)
        self.assertEqual(before, self.formal_hashes()); self.assertFalse((self.jobs / 'apply.lock').exists())
        journal = core.read_json(out / 'transaction.json')
        self.assertEqual('rolled_back', journal['phase']); self.assertGreater(len(journal['entries']), 5)
        self.assertIn('final readback mismatch', journal['validationError'])

    def test_unreadable_lock_is_not_deleted_or_bypassed(self):
        (self.jobs / 'apply.lock').write_text('cannot-identify-owner')
        with self.assertRaisesRegex(RuntimeError, 'Unreadable apply lock'):
            with core.job_lock(): self.fail('invalid lock owner was bypassed')
        self.assertEqual('cannot-identify-owner', (self.jobs / 'apply.lock').read_text())

    def test_cancel_safe_boundary_preserves_formal_files(self):
        plan = self.minimal_plan(); before = self.formal_hashes(); out = self.jobs / 'cancelled'; out.mkdir()
        (out / 'cancel.request').write_text('cancel')
        with mock.patch.object(core, 'validate', return_value={'passed': True}):
            with self.assertRaisesRegex(RuntimeError, 'Cancelled'): core.apply_plan(plan, out)
        self.assertEqual(before, self.formal_hashes()); self.assertFalse((self.jobs / 'apply.lock').exists())

    def test_source_hash_change_rejects_stale_candidate(self):
        plan = self.minimal_plan(); (self.formal / 'stable.json').write_text('external source edit')
        protected = self.formal_hashes()
        with mock.patch.object(core, 'validate', return_value={'passed': True}):
            with self.assertRaisesRegex(RuntimeError, 'External source changes'): core.apply_plan(plan, self.jobs / 'stale-candidate')
        self.assertEqual(protected, self.formal_hashes())

    def test_missing_luban_dependency_never_publishes_staged_files(self):
        plan = self.minimal_plan(); before = self.formal_hashes()
        with mock.patch.object(core, 'validate', return_value={'passed': True}), mock.patch.object(core, 'excel_write', side_effect=self.stage_excel_fixture):
            with self.assertRaisesRegex(RuntimeError, 'Missing Luban executable'): core.apply_plan(plan, self.jobs / 'missing-luban')
        self.assertEqual(before, self.formal_hashes()); self.assertFalse((self.jobs / 'apply.lock').exists())

    def test_luban_process_failure_retains_formal_and_diagnostic_log(self):
        plan = self.minimal_plan(); before = self.formal_hashes()
        executable = self.root / 'Luban/Tools/Luban.ClientServer/Luban.ClientServer.exe'; executable.parent.mkdir(parents=True); executable.write_bytes(b'placeholder resolved dependency')
        result = subprocess.CompletedProcess(['Luban'], 17, stdout='injected generator failure', stderr='bad data reference')
        with mock.patch.object(core, 'validate', return_value={'passed': True}), mock.patch.object(core, 'excel_write', side_effect=self.stage_excel_fixture), mock.patch.object(core.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(RuntimeError, 'Luban failed'): core.apply_plan(plan, self.jobs / 'luban-failure')
        self.assertEqual(before, self.formal_hashes())
        log = self.jobs / 'luban-failure/luban.cache.log'
        self.assertIn('bad data reference', log.read_text(encoding='utf-8')); self.assertFalse((self.jobs / 'apply.lock').exists())

    def test_mid_stage_cancel_retains_formal_files(self):
        plan = self.minimal_plan(); before = self.formal_hashes(); out = self.jobs / 'cancel-during-excel'
        def cancelled_stage(stage, candidate):
            self.stage_excel_fixture(stage, candidate); (out / 'cancel.request').write_text('cancel during staging')
        with mock.patch.object(core, 'validate', return_value={'passed': True}), mock.patch.object(core, 'excel_write', side_effect=cancelled_stage):
            with self.assertRaisesRegex(RuntimeError, 'Cancelled'): core.apply_plan(plan, out)
        self.assertEqual(before, self.formal_hashes()); self.assertFalse((self.jobs / 'apply.lock').exists())

    @unittest.skipUnless(os.name == 'nt', 'Native Windows file-sharing lock scenario')
    def test_real_excel_file_lock_fails_staging_without_formal_changes(self):
        import ctypes
        from ctypes import wintypes
        import openpyxl
        workbook = self.data / 'EnemyData.xlsx'
        wb = openpyxl.Workbook(); wb.active.append(['id', 'hp']); wb.save(workbook); wb.close()
        before = self.formal_hashes(); plan = self.minimal_plan()
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE; kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.CreateFileW(str(workbook), 0x80000000, 0, None, 3, 0x80, None)
        self.assertNotEqual(wintypes.HANDLE(-1).value, handle, ctypes.get_last_error())
        def stage_locked(stage, candidate):
            stage.mkdir(parents=True, exist_ok=True)
            core.shutil.copy2(workbook, stage / workbook.name)
        try:
            with mock.patch.object(core, 'validate', return_value={'passed': True}), mock.patch.object(core, 'excel_write', side_effect=stage_locked):
                with self.assertRaises(PermissionError): core.apply_plan(plan, self.jobs / 'locked-excel')
        finally: kernel.CloseHandle(handle)
        self.assertEqual(before, self.formal_hashes()); self.assertFalse((self.jobs / 'apply.lock').exists())

    @unittest.skipUnless(os.name == 'nt', 'Native Windows file-sharing lock scenario')
    def test_real_excel_commit_lock_rolls_back_earlier_files_without_rewriting_locked_original(self):
        import ctypes
        from ctypes import wintypes
        import openpyxl
        workbook = self.data / 'EnemyData.xlsx'
        wb = openpyxl.Workbook(); wb.active.append(['id', 'hp']); wb.save(workbook); wb.close()
        files = self.files(); before = self.formal_hashes()
        # Share reads so backup and source hashing work, but deny replacement as Excel does.
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE; kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.CreateFileW(str(workbook), 0x80000000, 1, None, 3, 0x80, None)
        self.assertNotEqual(wintypes.HANDLE(-1).value, handle, ctypes.get_last_error())
        staged_workbook = self.jobs / 'job/stage/locked.xlsx'; staged_workbook.write_bytes(b'new workbook cannot replace locked target')
        try:
            with self.assertRaises(PermissionError):
                core.commit_files(files[:2] + [(staged_workbook, workbook)], self.jobs / 'job', {'profileId': 'D04'})
            self.assertEqual(before, self.formal_hashes())
            self.assertEqual('rolled_back', core.read_json(self.jobs / 'job/transaction.json')['phase'])
        finally: kernel.CloseHandle(handle)


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.records = []
    def startTest(self, test): self.started = time.perf_counter(); super().startTest(test)
    def record(self, test, status, detail=None): self.records.append({'test': test.id().split('.')[-1], 'status': status, 'seconds': round(time.perf_counter() - self.started, 6), 'detail': detail})
    def addSuccess(self, test): super().addSuccess(test); self.record(test, 'passed')
    def addFailure(self, test, err): super().addFailure(test, err); self.record(test, 'failed', self._exc_info_to_string(err, test))
    def addError(self, test, err): super().addError(test, err); self.record(test, 'error', self._exc_info_to_string(err, test))
    def addSkip(self, test, reason): super().addSkip(test, reason); self.record(test, 'skipped', reason)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', default=str(REAL_ROOT / 'Docs/BalanceEvidence/pipeline-transaction-tests.json')); args = parser.parse_args()
    started = time.perf_counter()
    # Read-only evidence that the actual project files were not modified by any fixture.
    protected = [REAL_ROOT / 'Assets/ConfigJson', REAL_ROOT / 'Assets/Gen', REAL_ROOT / 'Luban/Config/Datas', REAL_ROOT / 'Luban/BalanceDesign']
    before = {str(p.relative_to(REAL_ROOT)): core.file_hash(p) for parent in protected for p in parent.rglob('*') if p.is_file()}
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TransactionFaultTests)
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    after = {str(p.relative_to(REAL_ROOT)): core.file_hash(p) for parent in protected for p in parent.rglob('*') if p.is_file()}
    report = {'schemaVersion': 1, 'suite': 'Actual balance_pipeline transaction core with isolated temporary roots', 'actualCoreSha256': core.file_hash(pathlib.Path(__file__).with_name('balance_pipeline.py')), 'passed': result.wasSuccessful() and before == after, 'testsRun': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'seconds': round(time.perf_counter() - started, 3), 'formalProjectHashesUnchanged': before == after, 'writeScope': 'Only TemporaryDirectory fixtures and this evidence JSON; no formal apply', 'mockBoundaries': 'Fault tests invoke real commit_files/job_lock/restore_transaction/assert_sources/check_cancel/luban_export. Full plan mathematics is excluded by stubbing validation for apply-failure boundaries; subprocess nonzero exit is injected, not an actual failed production export.', 'results': result.records}
    out = pathlib.Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'testsRun': result.testsRun, 'out': str(out)}, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__': sys.exit(main())
