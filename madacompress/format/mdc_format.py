import struct
import zlib
from typing import List, Tuple
from ..engine.triplet import LZ77Triplet

class MDCError(Exception):
    pass

class InvalidFormatError(MDCError):
    pass

class UnsupportedVersionError(MDCError):
    pass

class CorruptedFileError(MDCError):
    pass

class ChecksumMismatchError(MDCError):
    pass

class MDCHeader:
    MAGIC = b'MDC1'
    CURRENT_VERSION = 1
    ALGO_LZ77 = 1
    HEADER_SIZE = 28
    HEADER_STRUCT = '>4sHBBHHQII'

    def __init__(self, version: int=CURRENT_VERSION, algo_id: int=ALGO_LZ77, flags: int=0, search_buffer_size: int=4096, lookahead_buffer_size: int=256, original_size: int=0, original_crc32: int=0, triplet_count: int=0):
        self.version = version
        self.algo_id = algo_id
        self.flags = flags
        self.search_buffer_size = search_buffer_size
        self.lookahead_buffer_size = lookahead_buffer_size
        self.original_size = original_size
        self.original_crc32 = original_crc32
        self.triplet_count = triplet_count

    def pack(self) -> bytes:
        return struct.pack(self.HEADER_STRUCT, self.MAGIC, self.version, self.algo_id, self.flags, self.search_buffer_size, self.lookahead_buffer_size, self.original_size, self.original_crc32, self.triplet_count)

    @classmethod
    def unpack(cls, data: bytes) -> 'MDCHeader':
        if len(data) < cls.HEADER_SIZE:
            raise CorruptedFileError(f"Fichier trop court pour contenir l'en-tête MadaCompress ({len(data)} octets reçus, {cls.HEADER_SIZE} attendus).")
        magic, version, algo, flags, s_size, l_size, orig_size, crc, count = struct.unpack(cls.HEADER_STRUCT, data[:cls.HEADER_SIZE])
        if magic != cls.MAGIC:
            raise InvalidFormatError(f"Signature de format invalide ({magic!r}). Ce fichier n'est pas une archive .mdc reconnue.")
        if version != cls.CURRENT_VERSION:
            raise UnsupportedVersionError(f'Version de format non supportée ({version}). Version attendue : {cls.CURRENT_VERSION}.')
        if algo != cls.ALGO_LZ77:
            raise InvalidFormatError(f"Identifiant d'algorithme inconnu : {algo}.")
        return cls(version=version, algo_id=algo, flags=flags, search_buffer_size=s_size, lookahead_buffer_size=l_size, original_size=orig_size, original_crc32=crc, triplet_count=count)

class MDCFormat:
    TRIPLET_STRUCT = '>HHBB'
    TRIPLET_SIZE = 6

    @classmethod
    def serialize(cls, triplets: List[LZ77Triplet], original_data: bytes, search_buffer_size: int, lookahead_buffer_size: int) -> bytes:
        original_crc = zlib.crc32(original_data) & 4294967295
        header = MDCHeader(search_buffer_size=search_buffer_size, lookahead_buffer_size=lookahead_buffer_size, original_size=len(original_data), original_crc32=original_crc, triplet_count=len(triplets))
        payload = bytearray(header.pack())
        for t in triplets:
            has_sym = 1 if t.next_symbol is not None else 0
            if has_sym:
                if isinstance(t.next_symbol, int):
                    sym_val = t.next_symbol & 255
                elif isinstance(t.next_symbol, str):
                    sym_val = ord(t.next_symbol) & 255
                elif isinstance(t.next_symbol, (bytes, bytearray)):
                    sym_val = t.next_symbol[0] if len(t.next_symbol) > 0 else 0
                else:
                    sym_val = 0
            else:
                sym_val = 0
            payload.extend(struct.pack(cls.TRIPLET_STRUCT, min(65535, t.offset), min(65535, t.length), has_sym, sym_val))
        return bytes(payload)

    @classmethod
    def deserialize(cls, file_content: bytes) -> Tuple[MDCHeader, List[LZ77Triplet]]:
        header = MDCHeader.unpack(file_content)
        expected_total_size = MDCHeader.HEADER_SIZE + header.triplet_count * cls.TRIPLET_SIZE
        if len(file_content) < expected_total_size:
            raise CorruptedFileError(f'Archive .mdc corrompue ou tronquée : taille réelle ({len(file_content)} octets) inférieure à la taille attendue ({expected_total_size} octets pour {header.triplet_count} triplets).')
        triplets: List[LZ77Triplet] = []
        offset_ptr = MDCHeader.HEADER_SIZE
        for _ in range(header.triplet_count):
            chunk = file_content[offset_ptr:offset_ptr + cls.TRIPLET_SIZE]
            t_offset, t_length, has_sym, sym_val = struct.unpack(cls.TRIPLET_STRUCT, chunk)
            if has_sym not in (0, 1):
                raise CorruptedFileError(f'Archive .mdc corrompue : indicateur has_symbol invalide ({has_sym}).')
            next_sym = sym_val if has_sym == 1 else None
            triplets.append(LZ77Triplet(t_offset, t_length, next_sym))
            offset_ptr += cls.TRIPLET_SIZE
        return (header, triplets)
