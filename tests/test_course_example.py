import unittest
from madacompress.engine.lz77 import LZ77Engine

class TestCourseExample(unittest.TestCase):

    def test_cabracadabrarrarrad_exact_triplets(self):
        engine = LZ77Engine(search_buffer_size=LZ77Engine.COURSE_SEARCH_SIZE, lookahead_buffer_size=LZ77Engine.COURSE_LOOKAHEAD_SIZE)
        text = 'CABRACADABRARRARRAD'
        expected_triplets = [(0, 0, 'C'), (0, 0, 'A'), (0, 0, 'B'), (0, 0, 'R'), (3, 1, 'C'), (2, 1, 'D'), (7, 4, 'R'), (3, 5, 'D')]
        steps = list(engine.step_by_step_encode(text))
        actual_triplets = [s['triplet'].to_tuple() for s in steps]
        self.assertEqual(actual_triplets, expected_triplets, f'Les triplets produits diffèrent du cours !\nObtenu: {actual_triplets}\nAttendu: {expected_triplets}')
        triplets_objs = [s['triplet'] for s in steps]
        decoded = engine.decompress_text(triplets_objs)
        self.assertEqual(decoded, text)

    def test_step_by_step_buffers_content(self):
        engine = LZ77Engine(search_buffer_size=7, lookahead_buffer_size=6)
        text = 'CABRACADABRARRARRAD'
        steps = list(engine.step_by_step_encode(text))
        self.assertEqual(steps[0]['search_buffer'], '')
        self.assertEqual(steps[0]['lookahead_buffer'], 'CABRAC')
        self.assertEqual(steps[0]['triplet'].to_tuple(), (0, 0, 'C'))
        self.assertEqual(steps[0]['decoded_so_far'], 'C')
        self.assertEqual(steps[4]['triplet'].to_tuple(), (3, 1, 'C'))
        self.assertEqual(steps[4]['decoded_so_far'], 'CABRAC')
        self.assertEqual(steps[5]['triplet'].to_tuple(), (2, 1, 'D'))
        self.assertEqual(steps[5]['decoded_so_far'], 'CABRACAD')
        self.assertEqual(steps[6]['triplet'].to_tuple(), (7, 4, 'R'))
        self.assertEqual(steps[6]['decoded_so_far'], 'CABRACADABRAR')
        self.assertEqual(steps[7]['triplet'].to_tuple(), (3, 5, 'D'))
        self.assertEqual(steps[7]['decoded_so_far'], 'CABRACADABRARRARRAD')
if __name__ == '__main__':
    unittest.main()
