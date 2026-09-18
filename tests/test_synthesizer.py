import sys
import types
import unittest
from urllib.error import HTTPError
from unittest.mock import call, patch

sys.modules.setdefault('edge_tts',types.SimpleNamespace(Communicate=None))
from app import synthesizer


class _AudioResponse:
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self):return b'a'*1200


class AzureRegionTests(unittest.TestCase):
    def test_401_records_region_failure_then_refreshes_token(self):
        cfg={'voices_ttl_hours':24,'regions':['eastus']}
        unauthorized=HTTPError('https://eastus.example',401,'Unauthorized',None,None)
        with patch.object(synthesizer.voices,'find',return_value={'ShortName':'voice'}), \
             patch.object(synthesizer.regions,'needs_benchmark',return_value=False), \
             patch.object(synthesizer.token_manager,'get',side_effect=['old-token','new-token']) as get_token, \
             patch.object(synthesizer.token_manager,'invalidate') as invalidate, \
             patch.object(synthesizer.regions,'ordered',return_value=['eastus']), \
             patch.object(synthesizer.regions,'record') as record, \
             patch.object(synthesizer,'urlopen',side_effect=[unauthorized,_AudioResponse()]):
            data,region=synthesizer.azure('text','voice','+0%','+0Hz','+0%','','',cfg)
        self.assertEqual((data,region),(b'a'*1200,'eastus'))
        self.assertEqual(get_token.call_args_list,[call(force=False),call(force=True)])
        invalidate.assert_called_once_with()
        self.assertEqual(record.call_count,2)
        self.assertEqual(record.call_args_list[0].args[:2],('eastus',False))
        self.assertEqual(record.call_args_list[0].args[3],'HTTP 401')
        self.assertEqual(record.call_args_list[1].args[:2],('eastus',True))

    def test_repeated_401_marks_attempted_region_failures(self):
        cfg={'voices_ttl_hours':24,'regions':['eastus','westus']}
        unauthorized=HTTPError('https://eastus.example',401,'Unauthorized',None,None)
        with patch.object(synthesizer.voices,'find',return_value={'ShortName':'voice'}), \
             patch.object(synthesizer.regions,'needs_benchmark',return_value=False), \
             patch.object(synthesizer.token_manager,'get',side_effect=['old-token','new-token']), \
             patch.object(synthesizer.token_manager,'invalidate') as invalidate, \
             patch.object(synthesizer.regions,'ordered',return_value=['eastus','westus']), \
             patch.object(synthesizer.regions,'record') as record, \
             patch.object(synthesizer,'urlopen',side_effect=[unauthorized,unauthorized]) as urlopen:
            with self.assertRaisesRegex(RuntimeError,'authentication:401'):
                synthesizer.azure('text','voice','+0%','+0Hz','+0%','','',cfg)
        self.assertEqual(urlopen.call_count,2)
        self.assertEqual(invalidate.call_count,2)
        self.assertEqual(record.call_count,2)
        self.assertTrue(all(item.args[:2]==('eastus',False) for item in record.call_args_list))
        self.assertTrue(all(item.args[3]=='HTTP 401' for item in record.call_args_list))

    def test_benchmark_probes_every_enabled_region(self):
        cfg={'default_voice':'voice','voices_ttl_hours':24,'regions':['eastus','westus']}
        snapshot={'enabled':[],'disabled':[]}
        with patch.object(synthesizer.regions,'needs_benchmark',return_value=True), \
             patch.object(synthesizer.voices,'find',return_value={'ShortName':'voice'}), \
             patch.object(synthesizer.token_manager,'get',return_value='token'), \
             patch.object(synthesizer,'_request',return_value=b'a'*1200) as request, \
             patch.object(synthesizer.regions,'record') as record, \
             patch.object(synthesizer.regions,'status',return_value=snapshot):
            result=synthesizer.benchmark_regions(cfg)
        self.assertIs(result,snapshot)
        self.assertEqual(request.call_count,2)
        self.assertEqual({item.args[0] for item in request.call_args_list},{'eastus','westus'})
        self.assertEqual(record.call_count,2)
        self.assertTrue(all(item.kwargs['benchmark'] for item in record.call_args_list))

    def test_benchmark_401_records_region_failure(self):
        cfg={'default_voice':'voice','voices_ttl_hours':24,'regions':['eastus']}
        unauthorized=HTTPError('https://eastus.example',401,'Unauthorized',None,None)
        with patch.object(synthesizer.regions,'needs_benchmark',return_value=True), \
             patch.object(synthesizer.voices,'find',return_value={'ShortName':'voice'}), \
             patch.object(synthesizer.token_manager,'get',return_value='token'), \
             patch.object(synthesizer.token_manager,'invalidate') as invalidate, \
             patch.object(synthesizer,'_request',side_effect=unauthorized), \
             patch.object(synthesizer.regions,'record') as record, \
             patch.object(synthesizer.regions,'status',return_value={'enabled':[],'disabled':[]}):
            synthesizer.benchmark_regions(cfg)
        invalidate.assert_called_once_with()
        self.assertEqual(record.call_args.args[:2],('eastus',False))
        self.assertEqual(record.call_args.args[3],'HTTP 401')
        self.assertTrue(record.call_args.kwargs['benchmark'])

    def test_first_synthesis_runs_benchmark_before_audio_request(self):
        cfg={'default_voice':'voice','voices_ttl_hours':24,'regions':['eastus']}
        with patch.object(synthesizer.voices,'find',return_value={'ShortName':'voice'}), \
             patch.object(synthesizer.regions,'needs_benchmark',return_value=True), \
             patch.object(synthesizer,'benchmark_regions') as benchmark, \
             patch.object(synthesizer.token_manager,'get',return_value='token'), \
             patch.object(synthesizer.regions,'ordered',return_value=['eastus']), \
             patch.object(synthesizer.regions,'record'), \
             patch.object(synthesizer,'_request',return_value=b'a'*1200):
            synthesizer.azure('text','voice','+0%','+0Hz','+0%','','',cfg)
        benchmark.assert_called_once_with(cfg)


if __name__=='__main__':unittest.main()
