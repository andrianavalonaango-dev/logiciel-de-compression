from typing import Any, Callable, Generator, List, Optional, Tuple, Union
from .triplet import LZ77Triplet

class LZ77Engine:
    DEFAULT_SEARCH_SIZE = 4096
    DEFAULT_LOOKAHEAD_SIZE = 256
    COURSE_SEARCH_SIZE = 7
    COURSE_LOOKAHEAD_SIZE = 6

    def __init__(self, search_buffer_size: int=DEFAULT_SEARCH_SIZE, lookahead_buffer_size: int=DEFAULT_LOOKAHEAD_SIZE):
        if search_buffer_size < 1:
            raise ValueError('La taille du tampon de recherche doit être >= 1')
        if lookahead_buffer_size < 2:
            raise ValueError("La taille du tampon d'anticipation doit être >= 2")
        self.search_buffer_size = int(search_buffer_size)
        self.lookahead_buffer_size = int(lookahead_buffer_size)

    def compress(self, data: bytes, progress_callback: Optional[Callable[[int, int], None]]=None) -> List[LZ77Triplet]:
        if not data:
            return []
        triplets: List[LZ77Triplet] = []
        n = len(data)
        cursor = 0
        last_progress_update = 0
        while cursor < n:
            if progress_callback and (cursor - last_progress_update >= 4096 or cursor == n - 1):
                progress_callback(cursor, n)
                last_progress_update = cursor
            best_offset, best_length = self._find_longest_match(data, cursor, n)
            if best_length > 0:
                if cursor + best_length < n:
                    next_byte = data[cursor + best_length]
                    triplets.append(LZ77Triplet(best_offset, best_length, next_byte))
                    cursor += best_length + 1
                else:
                    if best_length > 1:
                        triplets.append(LZ77Triplet(best_offset, best_length - 1, data[n - 1]))
                    else:
                        triplets.append(LZ77Triplet(0, 0, data[n - 1]))
                    cursor = n
            else:
                triplets.append(LZ77Triplet(0, 0, data[cursor]))
                cursor += 1
        if progress_callback:
            progress_callback(n, n)
        return triplets

    def decompress(self, triplets: List[LZ77Triplet], expected_size: Optional[int]=None, progress_callback: Optional[Callable[[int, int], None]]=None) -> bytes:
        output = bytearray()
        total_triplets = len(triplets)
        for idx, triplet in enumerate(triplets):
            if progress_callback and (idx % 1024 == 0 or idx == total_triplets - 1):
                progress_callback(idx + 1, total_triplets)
            offset = triplet.offset
            length = triplet.length
            next_sym = triplet.next_symbol
            if length > 0:
                if offset <= 0:
                    raise ValueError(f'Triplet invalide : offset={offset} pour longueur={length}')
                if offset > len(output):
                    raise ValueError(f'Dépassement de tampon : offset {offset} > taille décodée actuelle {len(output)}')
                start_pos = len(output) - offset
                for k in range(length):
                    output.append(output[start_pos + k])
            if next_sym is not None:
                if isinstance(next_sym, int):
                    output.append(next_sym)
                elif isinstance(next_sym, str):
                    output.extend(next_sym.encode('utf-8'))
                elif isinstance(next_sym, (bytes, bytearray)):
                    output.extend(next_sym)
                else:
                    raise TypeError(f'Type de symbole non supporté : {type(next_sym)}')
            if expected_size is not None and len(output) > expected_size:
                raise ValueError(f'Taille décompressée ({len(output)}) dépasse la taille attendue ({expected_size})')
        if expected_size is not None and len(output) != expected_size:
            raise ValueError(f'Taille finale décompressée ({len(output)}) ne correspond pas à la taille attendue ({expected_size})')
        return bytes(output)

    def _find_longest_match(self, data: Union[bytes, str], cursor: int, total_len: int) -> Tuple[int, int]:
        best_offset = 0
        best_length = 0
        search_start = max(0, cursor - self.search_buffer_size)
        search_window_len = cursor - search_start
        if search_window_len <= 0:
            return (0, 0)
        max_possible_len = min(self.lookahead_buffer_size - 1, total_len - cursor - 1)
        if max_possible_len <= 0:
            return (0, 0)
        for offset in range(1, search_window_len + 1):
            match_len = 0
            while match_len < max_possible_len and data[cursor + match_len] == data[cursor - offset + match_len]:
                match_len += 1
            if match_len > best_length:
                best_length = match_len
                best_offset = offset
        return (best_offset, best_length)

    def step_by_step_encode(self, text: str) -> Generator[dict, None, None]:
        n = len(text)
        cursor = 0
        step_number = 1
        decoded_builder: List[str] = []
        while cursor < n:
            search_start = max(0, cursor - self.search_buffer_size)
            search_buf = text[search_start:cursor]
            lookahead_end = min(n, cursor + self.lookahead_buffer_size)
            lookahead_buf = text[cursor:lookahead_end]
            best_offset, best_length = self._find_longest_match(text, cursor, n)
            if best_length > 0:
                matched_str = text[cursor:cursor + best_length]
                if cursor + best_length < n:
                    next_char = text[cursor + best_length]
                    triplet = LZ77Triplet(best_offset, best_length, next_char)
                    cursor += best_length + 1
                else:
                    if best_length > 1:
                        matched_str = text[cursor:cursor + best_length - 1]
                        triplet = LZ77Triplet(best_offset, best_length - 1, text[n - 1])
                    else:
                        matched_str = ''
                        triplet = LZ77Triplet(0, 0, text[n - 1])
                    cursor = n
            else:
                matched_str = ''
                triplet = LZ77Triplet(0, 0, text[cursor])
                cursor += 1
            if triplet.length > 0:
                start_p = len(decoded_builder) - triplet.offset
                for k in range(triplet.length):
                    decoded_builder.append(decoded_builder[start_p + k])
            if triplet.next_symbol:
                decoded_builder.append(str(triplet.next_symbol))
            yield {'step': step_number, 'cursor': cursor, 'search_buffer': search_buf, 'lookahead_buffer': lookahead_buf, 'triplet': triplet, 'matched_string': matched_str, 'decoded_so_far': ''.join(decoded_builder), 'explanation': triplet.explain()}
            step_number += 1

    def compress_text(self, text: str) -> List[LZ77Triplet]:
        return [step['triplet'] for step in self.step_by_step_encode(text)]

    def decompress_text(self, triplets: List[LZ77Triplet]) -> str:
        out_bytes = self.decompress(triplets)
        return out_bytes.decode('utf-8')
