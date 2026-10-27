"""Reject false-positive native reopen evidence without accessing game profiles."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.test_android_emulator import verify_reopened_report, wait_for_report


def reports():
    first=dict(passed=True,platform='android',schema=5,reopened_process=False,
               profile='/private/qa-tamanhos-v1/save.json',reopen_snapshot_sha256='a'*64)
    return first,{**first,'reopened_process':True}


class NativeReopenEvidenceTests(unittest.TestCase):
    def test_valid_second_process_is_accepted(self):
        verify_reopened_report(*reports())

    def test_failing_or_non_native_process_is_rejected(self):
        for target in (0,1):
            for key,value in (('passed',False),('passed',1),('platform','offscreen')):
                pair=list(reports());pair[target][key]=value
                with self.subTest(target=target,key=key,value=value),self.assertRaises(RuntimeError):
                    verify_reopened_report(*pair)

    def test_schema_and_stage_evidence_cannot_be_missing_or_wrong(self):
        for target in (0,1):
            for value in (None,4,6,5.0,'5'):
                pair=list(reports());pair[target]['schema']=value
                with self.subTest(target=target,schema=value),self.assertRaises(RuntimeError):
                    verify_reopened_report(*pair)
        for target,value in ((0,True),(0,None),(1,False),(1,None)):
            pair=list(reports());pair[target]['reopened_process']=value
            with self.subTest(target=target,reopened=value),self.assertRaises(RuntimeError):
                verify_reopened_report(*pair)

    def test_relaunch_cannot_select_a_new_profile(self):
        first,reopened=reports();reopened['profile']='/private/other-context/save.json'
        with self.assertRaisesRegex(RuntimeError,'different profile'):
            verify_reopened_report(first,reopened)

    def test_snapshot_fingerprint_is_required_and_must_match(self):
        for value in (None,'','a'*63,'A'*64,'g'*64):
            first,reopened=reports();first['reopen_snapshot_sha256']=value
            with self.subTest(value=value),self.assertRaises(RuntimeError):
                verify_reopened_report(first,reopened)
        first,reopened=reports();reopened['reopen_snapshot_sha256']='b'*64
        with self.assertRaisesRegex(RuntimeError,'durable snapshot'):
            verify_reopened_report(first,reopened)

    def test_partial_log_line_is_not_accepted_as_complete_evidence(self):
        with tempfile.TemporaryDirectory(prefix='pesca-host-harness-') as folder:
            logs=['PESCA_QA_RESULT={"passed":', 'PESCA_QA_RESULT={"passed":true}']
            with patch('tools.test_android_emulator.call',side_effect=logs), \
                    patch('tools.test_android_emulator.time.sleep'):
                report=wait_for_report('synthetic-adb',Path(folder),'synthetic-log.txt',timeout=1)
            self.assertEqual(report,{'passed':True})

    def test_optimized_interpreter_still_rejects_snapshot_mismatch(self):
        script="""from tools.test_android_emulator_harness import reports
from tools.test_android_emulator import verify_reopened_report
first,reopened=reports();reopened['reopen_snapshot_sha256']='b'*64
try:verify_reopened_report(first,reopened)
except RuntimeError:print('rejected')
else:raise RuntimeError('False positive under optimize=2')
"""
        result=subprocess.run([sys.executable,'-OO','-B','-c',script],
                              cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'rejected')


if __name__=='__main__':unittest.main(verbosity=2)
