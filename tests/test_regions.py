import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import regions


class RegionHealthTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir=tempfile.TemporaryDirectory()
        self.original_path=regions.PATH
        regions.PATH=str(Path(self.temp_dir.name)/'regions.json')

    def tearDown(self):
        regions.PATH=self.original_path
        self.temp_dir.cleanup()

    def test_success_is_healthy_and_clears_current_error(self):
        with patch('app.regions.time.time',return_value=1000):regions.record('eastus',False,1.2,'TimeoutError')
        with patch('app.regions.time.time',return_value=1010):
            regions.record('eastus',True,0.4)
            current=regions.status(['eastus'])['enabled'][0]
        self.assertEqual(current['state'],'healthy')
        self.assertEqual(current['consecutive_failures'],0)
        self.assertEqual(current['last_error'],'')
        self.assertEqual(current['last_failure'],0)

    def test_three_consecutive_failures_are_unavailable(self):
        with patch('app.regions.time.time',return_value=1000):
            for _ in range(3):regions.record('eastus',False,1,'TimeoutError')
            current=regions.status(['eastus'])['enabled'][0]
        self.assertEqual(current['state'],'unavailable')

    def test_one_failure_after_success_is_degraded(self):
        with patch('app.regions.time.time',return_value=1000):regions.record('eastus',True,0.2)
        with patch('app.regions.time.time',return_value=1010):
            regions.record('eastus',False,1,'TimeoutError')
            current=regions.status(['eastus'])['enabled'][0]
        self.assertEqual(current['state'],'degraded')

    def test_old_success_is_stale(self):
        Path(regions.PATH).write_text(json.dumps({'eastus':{'successes':1,'last_attempt':1,'last_success':1,'avg_latency':0.2}}),encoding='utf-8')
        with patch('app.regions.time.time',return_value=regions.STALE_SECONDS+2):current=regions.status(['eastus'])['enabled'][0]
        self.assertEqual(current['state'],'stale')

    def test_disabled_regions_are_separated_from_enabled(self):
        Path(regions.PATH).write_text(json.dumps({'westus':{'successes':2,'last_attempt':10,'last_success':10}}),encoding='utf-8')
        snapshot=regions.status(['eastus'])
        self.assertEqual([x['id'] for x in snapshot['enabled']],['eastus'])
        self.assertEqual([x['id'] for x in snapshot['disabled']],['westus'])

    def test_legacy_statistics_are_supported(self):
        Path(regions.PATH).write_text(json.dumps({'eastus':{'successes':2,'failures':1,'avg_latency':0.5,'last_success':10,'last_error':'old'}}),encoding='utf-8')
        with patch('app.regions.time.time',return_value=20):current=regions.status(['eastus'])['enabled'][0]
        self.assertEqual(current['state'],'healthy')
        self.assertEqual(current['successes'],2)
        self.assertEqual(current['last_error'],'')

    def test_equal_health_preserves_configured_priority(self):
        self.assertEqual(regions.ordered(['westus','eastus']),['westus','eastus'])


if __name__=='__main__':unittest.main()
