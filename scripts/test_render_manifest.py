import tempfile
import unittest
from pathlib import Path

from render_manifest import load_checksums


class RenderManifestTests(unittest.TestCase):
    def test_checksum_paths_are_keyed_by_asset_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SHA256SUMS.txt"
            path.write_text(
                f"{'0' * 64}  dist/attest-windows-x86_64.zip\n",
                encoding="utf-8",
            )

            self.assertEqual(
                load_checksums(path),
                {"attest-windows-x86_64.zip": "0" * 64},
            )


if __name__ == "__main__":
    unittest.main()
