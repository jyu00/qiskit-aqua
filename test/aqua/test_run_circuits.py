# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test the run_circuits function."""

import time
from unittest.mock import MagicMock

from qiskit.test.reference_circuits import ReferenceCircuits
from qiskit.test.mock.backends.vigo.fake_vigo import FakeVigo
from qiskit.test.mock.fake_job import FakeJob
from qiskit.compiler.assemble import assemble
from qiskit.providers.jobstatus import JOB_FINAL_STATES, JobStatus
from qiskit.aqua.utils.run_circuits import run_qobj

from test.aqua import QiskitAquaTestCase


class TestRunCircuits(QiskitAquaTestCase):
    """ Test Skip Qobj Validation """
    def setUp(self):
        super().setUp()

        self.qc = ReferenceCircuits.bell()
        self.qobj = assemble(self.qc)

    def test_job_status_callback(self):
        """Test job status callback."""

        def _job_callback(c_job_id, c_job_status, c_queue_pos, c_job):
            """Job status callback function."""
            # pylint: disable=unused-argument
            self.assertEqual(c_job_id, job_id)
            if c_job_status in JOB_FINAL_STATES:
                called['finished'] = True
            else:
                called['unfinished'] = True

        called = {'unfinished': False, 'finished': False}
        job_id = '123456'
        backend = PatchedFakeBackend(job_id)
        run_qobj(self.qobj, backend, job_callback=_job_callback)
        self.assertTrue(called['unfinished'], "Callback not invoked before job finished.")
        self.assertTrue(called['finished'], "Callback not invoked after job finished.")

    def test_job_status_callback_real(self):
        """Test job status callback."""

        def _job_callback(c_job_id, c_job_status, c_queue_pos, c_job):
            """Job status callback function."""
            # pylint: disable=unused-argument
            print(f"job id is {c_job_id}, job status {c_job_status}, queue pos {c_queue_pos}")
            # self.assertEqual(c_job_id, job_id)
            if c_job_status in JOB_FINAL_STATES:
                called['finished'] = True
            else:
                called['unfinished'] = True

        called = {'unfinished': False, 'finished': False}

        from qiskit import IBMQ, transpile, assemble
        provider = IBMQ.load_account()
        backend = provider.get_backend('ibmq_vigo')
        qobj = assemble(transpile(self.qc, backend=backend), backend=backend)
        run_qobj(qobj, backend, job_callback=_job_callback)
        self.assertTrue(called['unfinished'], "Callback not invoked before job finished.")
        self.assertTrue(called['finished'], "Callback not invoked after job finished.")


class PatchedFakeBackend(FakeVigo):
    """Patched fake backend that doesn't actually run a job."""

    def __init__(self, job_id='12345'):
        super().__init__()
        self.job_id = job_id

    def run(self, qobj):
        """Return a fake job"""
        job = PatchedFakeJob(self, self.job_id, self._fake_job_submit, qobj)
        job.submit()
        return job

    def _fake_job_submit(self, qobj):
        """Simulate job processing by sleeping for a while."""
        # pylint: disable=unused-argument
        time.sleep(5)


class PatchedFakeJob(FakeJob):
    """Patched fake job."""

    def status(self):
        """Return job status."""
        # This is needed because FakeJob doesn't return a JobStatus instance.
        status = super().status()
        if isinstance(status, JobStatus):
            return status
        return status['status']

    def result(self, timeout=None):
        """Return fake job result."""
        # This is needed because a MagicMock instance cannot be returned by a Future.
        result = MagicMock()
        result.success = True
        return result
