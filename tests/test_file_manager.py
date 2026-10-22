import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from madacompress.format.file_manager import FileManager
from madacompress.format.mdc_format import ChecksumMismatchError, CorruptedFileError

class TestFileManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_text_file_roundtrip(self):
        source_file = self.dir_path / 'sample.txt'
        compressed_file = self.dir_path / 'sample.txt.mdc'
        restored_file = self.dir_path / 'sample_restored.txt'
        original_content = 'Projet Universitaire MadaCompress\nAlgorithme LZ77 avec fenêtres glissantes.\nCABRACADABRARRARRAD\nRépétition de lignes pour tester le gain en espace :\n' + 'Ligne répétée pour observer la compression LZ77.\n' * 50
        source_file.write_bytes(original_content.encode('utf-8'))
        comp_stats = FileManager.compress_file(str(source_file), str(compressed_file))
        self.assertTrue(compressed_file.exists())
        self.assertGreater(comp_stats['compressed_size'], 0)
        decomp_stats = FileManager.decompress_file(str(compressed_file), str(restored_file))
        self.assertTrue(restored_file.exists())
        self.assertEqual(decomp_stats['restored_size'], len(original_content.encode('utf-8')))
        restored_content = restored_file.read_bytes().decode('utf-8')
        self.assertEqual(restored_content, original_content)

    def test_binary_file_roundtrip(self):
        source_bin = self.dir_path / 'binary_test.bin'
        compressed_bin = self.dir_path / 'binary_test.bin.mdc'
        restored_bin = self.dir_path / 'binary_restored.bin'
        binary_data = bytes([i % 256 for i in range(1024)]) + bytes([170, 85, 255, 0]) * 512
        source_bin.write_bytes(binary_data)
        original_hash = hashlib.sha256(binary_data).hexdigest()
        FileManager.compress_file(str(source_bin), str(compressed_bin))
        self.assertTrue(compressed_bin.exists())
        FileManager.decompress_file(str(compressed_bin), str(restored_bin))
        self.assertTrue(restored_bin.exists())
        restored_data = restored_bin.read_bytes()
        restored_hash = hashlib.sha256(restored_data).hexdigest()
        self.assertEqual(restored_hash, original_hash)
        self.assertEqual(restored_data, binary_data)

    def test_corrupted_file_detection(self):
        source_file = self.dir_path / 'to_corrupt.txt'
        compressed_file = self.dir_path / 'to_corrupt.txt.mdc'
        dest_file = self.dir_path / 'failed_output.txt'
        source_file.write_bytes('Données sensibles à protéger avec le CRC32 de MadaCompress.'.encode('utf-8'))
        FileManager.compress_file(str(source_file), str(compressed_file))
        corrupted_bytes = bytearray(compressed_file.read_bytes())
        corrupted_bytes[-1] ^= 85
        compressed_file.write_bytes(corrupted_bytes)
        with self.assertRaises((ChecksumMismatchError, CorruptedFileError)):
            FileManager.decompress_file(str(compressed_file), str(dest_file))

    def test_decompression_in_separate_process(self):
        source_file = self.dir_path / 'process_test.txt'
        compressed_file = self.dir_path / 'process_test.txt.mdc'
        restored_file = self.dir_path / 'process_test_restored.txt'
        content = 'Test de persistance inter-processus MadaCompress.\n' * 20
        source_file.write_text(content, encoding='utf-8')
        FileManager.compress_file(str(source_file), str(compressed_file))
        self.assertTrue(compressed_file.exists())
        py_cmd = f"import sys; sys.path.insert(0, '.'); from madacompress.format.file_manager import FileManager; FileManager.decompress_file(r'{compressed_file}', r'{restored_file}')"
        result = subprocess.run([sys.executable, '-c', py_cmd], cwd=str(Path('.').resolve()), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f'Le sous-processus de décompression a échoué :\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}')
        self.assertTrue(restored_file.exists())
        self.assertEqual(restored_file.read_text(encoding='utf-8'), content)
if __name__ == '__main__':
    unittest.main()
