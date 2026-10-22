import unittest
from madacompress.engine.lz77 import LZ77Engine
from madacompress.engine.triplet import LZ77Triplet

class TestLZ77Engine(unittest.TestCase):

    def setUp(self):
        self.engine = LZ77Engine(search_buffer_size=2048, lookahead_buffer_size=256)

    def test_empty_input(self):
        triplets = self.engine.compress(b'')
        self.assertEqual(triplets, [])
        decoded = self.engine.decompress(triplets, expected_size=0)
        self.assertEqual(decoded, b'')
        text_triplets = self.engine.compress_text('')
        self.assertEqual(text_triplets, [])
        text_decoded = self.engine.decompress_text(text_triplets)
        self.assertEqual(text_decoded, '')

    def test_single_character(self):
        data = b'A'
        triplets = self.engine.compress(data)
        self.assertEqual(len(triplets), 1)
        self.assertEqual(triplets[0], (0, 0, ord('A')))
        decoded = self.engine.decompress(triplets, expected_size=1)
        self.assertEqual(decoded, data)

    def test_no_repetitions(self):
        data = b'abcdefghij'
        triplets = self.engine.compress(data)
        self.assertEqual(len(triplets), len(data))
        for t in triplets:
            self.assertEqual(t.offset, 0)
            self.assertEqual(t.length, 0)
        decoded = self.engine.decompress(triplets, expected_size=len(data))
        self.assertEqual(decoded, data)

    def test_heavy_repetitions_and_overlap(self):
        data = b'A' * 50
        triplets = self.engine.compress(data)
        self.assertLess(len(triplets), 10)
        decoded = self.engine.decompress(triplets, expected_size=len(data))
        self.assertEqual(decoded, data)

    def test_utf8_accented_characters(self):
        sample_text = 'Université de Madagascar : compression & décompression LZ77 ! Éléphant naïf sous la forêt enchantée, à Noël. Ça marche parfaitement 🌟🚀'
        data = sample_text.encode('utf-8')
        triplets = self.engine.compress(data)
        decoded = self.engine.decompress(triplets, expected_size=len(data))
        self.assertEqual(decoded, data)
        self.assertEqual(decoded.decode('utf-8'), sample_text)

    def test_binary_data(self):
        data = bytes(range(256)) * 8
        triplets = self.engine.compress(data)
        decoded = self.engine.decompress(triplets, expected_size=len(data))
        self.assertEqual(decoded, data)

    def test_small_window_sizes(self):
        small_engine = LZ77Engine(search_buffer_size=2, lookahead_buffer_size=2)
        data = b'ANANAS_BANANE_ANANAS'
        triplets = small_engine.compress(data)
        decoded = small_engine.decompress(triplets, expected_size=len(data))
        self.assertEqual(decoded, data)

    def test_idempotency(self):
        samples = [b'Lorem ipsum dolor sit amet, consectetur adipiscing elit.', b'ABABABABABABABABABABABABABABABABABAB', b'TOBEORNOTTOBETHATISTHEQUESTION', bytes([0, 255, 0, 255, 18, 52, 86, 120] * 16)]
        for sample in samples:
            with self.subTest(sample=sample[:15]):
                compressed = self.engine.compress(sample)
                decompressed = self.engine.decompress(compressed, expected_size=len(sample))
                self.assertEqual(decompressed, sample)
if __name__ == '__main__':
    unittest.main()
