import hashlib
import io
import unittest
from unittest.mock import patch

from render_manifest import verify_downloads


class DownloadTests(unittest.TestCase):
    def test_valid_download_matches_release_checksum(self):
        data = b'release artifact'
        with patch('render_manifest.urllib.request.urlopen', return_value=io.BytesIO(data)) as request:
            verify_downloads('{{SHA256:app.exe}}', {'app.exe': hashlib.sha256(data).hexdigest()}, 'https://example.com/release')
        self.assertEqual(request.call_args.args[0], 'https://example.com/release/app.exe')

    def test_tampered_download_is_rejected(self):
        with patch('render_manifest.urllib.request.urlopen', return_value=io.BytesIO(b'tampered')):
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                verify_downloads('{{SHA256:app.exe}}', {'app.exe': '0' * 64}, 'https://example.com/release')

    def test_missing_hash_or_path_is_rejected_before_download(self):
        with patch('render_manifest.urllib.request.urlopen') as request:
            for asset in ('app.exe', '../source.zip'):
                with self.assertRaises(ValueError):
                    verify_downloads('{{SHA256:' + asset + '}}', {}, 'https://example.com/release')
        request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
