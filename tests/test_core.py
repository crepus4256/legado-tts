import concurrent.futures
import json
import tempfile
import unittest
from pathlib import Path

from app import audio_cache, config_store


class ConfigStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = config_store.PATH
        config_store.PATH = str(Path(self.temp_dir.name) / 'config.json')

    def tearDown(self):
        config_store.PATH = self.original_path
        self.temp_dir.cleanup()

    def test_valid_config_is_saved(self):
        saved = config_store.save({'cache_ttl_days': 30, 'regions': ['eastus']})
        self.assertEqual(saved['cache_ttl_days'], 30)
        self.assertEqual(config_store.load()['regions'], ['eastus'])

    def test_invalid_config_is_rejected_without_overwriting(self):
        config_store.save({'cache_ttl_days': 30})
        with self.assertRaises(ValueError):
            config_store.save({'cache_ttl_days': -1})
        self.assertEqual(config_store.load()['cache_ttl_days'], 30)

    def test_invalid_values_on_disk_fall_back_to_defaults(self):
        Path(config_store.PATH).write_text(json.dumps({'regions': None, 'cache_enabled': 'false'}), encoding='utf-8')
        loaded = config_store.load()
        self.assertEqual(loaded['regions'], config_store.DEFAULTS['regions'])
        self.assertIs(loaded['cache_enabled'], True)


class AudioCacheTests(unittest.TestCase):
    def test_concurrent_writes_use_unique_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            original_root = audio_cache.ROOT
            audio_cache.ROOT = directory
            try:
                payload = b'audio' * 1000
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    list(executor.map(lambda _: audio_cache.put('same-key', payload), range(32)))
                self.assertEqual(audio_cache.get('same-key', 1), payload)
                self.assertEqual(list(Path(directory).glob('*.tmp')), [])
            finally:
                audio_cache.ROOT = original_root


if __name__ == '__main__':
    unittest.main()
