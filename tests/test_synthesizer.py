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
    def test_401_refreshes_token_without_recording_region_failure(self):
        cfg={'voices_ttl_hours':24,'regions':['eastus']}
        unauthorized=HTTPError('https://eastus.example',401,'Unauthorized',None,None)
        with patch.object(synthesizer.voices,'find',return_value={'ShortName':'voice'}), \
             patch.object(synthesizer.token_manager,'get',side_effect=['old-token','new-token']) as get_token, \
             patch.object(synthesizer.token_manager,'invalidate') as invalidate, \
             patch.object(synthesizer.regions,'ordered',return_value=['eastus']), \
             patch.object(synthesizer.regions,'record') as record, \
             patch.object(synthesizer,'urlopen',side_effect=[unauthorized,_AudioResponse()]):
            data,region=synthesizer.azure('text','voice','+0%','+0Hz','+0%','','',cfg)
        self.assertEqual((data,region),(b'a'*1200,'eastus'))
        self.assertEqual(get_token.call_args_list,[call(force=False),call(force=True)])
        invalidate.assert_called_once_with()
        self.assertEqual(record.call_count,1)
        self.assertEqual(record.call_args.args[:2],('eastus',True))

    def test_repeated_401_does_not_mark_any_region_unavailable(self):
        cfg={'voices_ttl_hours':24,'regions':['eastus','westus']}
        unauthorized=HTTPError('https://eastus.example',401,'Unauthorized',None,None)
        with patch.object(synthesizer.voices,'find',return_value={'ShortName':'voice'}), \
             patch.object(synthesizer.token_manager,'get',side_effect=['old-token','new-token']), \
             patch.object(synthesizer.token_manager,'invalidate') as invalidate, \
             patch.object(synthesizer.regions,'ordered',return_value=['eastus','westus']), \
             patch.object(synthesizer.regions,'record') as record, \
             patch.object(synthesizer,'urlopen',side_effect=[unauthorized,unauthorized]) as urlopen:
            with self.assertRaisesRegex(RuntimeError,'authentication:401'):
                synthesizer.azure('text','voice','+0%','+0Hz','+0%','','',cfg)
        self.assertEqual(urlopen.call_count,2)
        self.assertEqual(invalidate.call_count,2)
        record.assert_not_called()


if __name__=='__main__':unittest.main()
