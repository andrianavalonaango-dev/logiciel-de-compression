import unittest
import struct
import zlib
from madacompress.engine.triplet import LZ77Triplet
from madacompress.format.mdc_format import MDCHeader, MDCFormat, InvalidFormatError, UnsupportedVersionError, CorruptedFileError

class TestMDCFormat(unittest.TestCase):

    def setUp(self):
        self.sample_data = b'MadaCompress 2026 : test de robustesse du format .mdc.'
        self.triplets = [LZ77Triplet(0, 0, ord('M')), LZ77Triplet(0, 0, ord('a')), LZ77Triplet(0, 0, ord('d')), LZ77Triplet(2, 1, ord('a'))]

    def test_serialize_and_deserialize_valid(self):
        serialized = MDCFormat.serialize(triplets=self.triplets, original_data=self.sample_data, search_buffer_size=4096, lookahead_buffer_size=256)
        header, unpacked_triplets = MDCFormat.deserialize(serialized)
        self.assertEqual(header.version, 1)
        self.assertEqual(header.algo_id, 1)
        self.assertEqual(header.search_buffer_size, 4096)
        self.assertEqual(header.lookahead_buffer_size, 256)
        self.assertEqual(header.original_size, len(self.sample_data))
        self.assertEqual(header.original_crc32, zlib.crc32(self.sample_data) & 4294967295)
        self.assertEqual(header.triplet_count, len(self.triplets))
        self.assertEqual(unpacked_triplets, self.triplets)

    def test_invalid_magic_signature(self):
        serialized = bytearray(MDCFormat.serialize(triplets=self.triplets, original_data=self.sample_data, search_buffer_size=4096, lookahead_buffer_size=256))
        serialized[0:4] = b'BAD!'
        with self.assertRaises(InvalidFormatError):
            MDCFormat.deserialize(bytes(serialized))

    def test_unsupported_version(self):
        serialized = bytearray(MDCFormat.serialize(triplets=self.triplets, original_data=self.sample_data, search_buffer_size=4096, lookahead_buffer_size=256))
        struct.pack_into('>H', serialized, 4, 99)
        with self.assertRaises(UnsupportedVersionError):
            MDCFormat.deserialize(bytes(serialized))

    def test_truncated_file(self):
        serialized = MDCFormat.serialize(triplets=self.triplets, original_data=self.sample_data, search_buffer_size=4096, lookahead_buffer_size=256)
        truncated = serialized[:len(serialized) - 3]
        with self.assertRaises(CorruptedFileError):
            MDCFormat.deserialize(truncated)
        header_truncated = serialized[:15]
        with self.assertRaises(CorruptedFileError):
            MDCFormat.deserialize(header_truncated)
if __name__ == '__main__':
    unittest.main()
