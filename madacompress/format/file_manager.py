import os
import zlib
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple
from ..engine.lz77 import LZ77Engine
from .mdc_format import ChecksumMismatchError, CorruptedFileError, InvalidFormatError, MDCFormat

class FileManager:

    @staticmethod
    def calculate_stats(source_size: int, compressed_size: int) -> Dict[str, float]:
        if source_size <= 0:
            return {'source_size': source_size, 'compressed_size': compressed_size, 'compression_ratio': 1.0, 'saving_percent': 0.0}
        ratio = compressed_size / source_size
        saving = (1.0 - ratio) * 100.0
        return {'source_size': source_size, 'compressed_size': compressed_size, 'compression_ratio': round(ratio, 4), 'saving_percent': round(saving, 2)}

    @classmethod
    def compress_file(cls, source_path: str, dest_path: Optional[str]=None, search_buffer_size: int=LZ77Engine.DEFAULT_SEARCH_SIZE, lookahead_buffer_size: int=LZ77Engine.DEFAULT_LOOKAHEAD_SIZE, progress_callback: Optional[Callable[[int, int], None]]=None) -> Dict[str, object]:
        src = Path(source_path).resolve()
        if not src.is_file():
            raise FileNotFoundError(f'Fichier source introuvable : {source_path}')
        if dest_path is None:
            dst = src.with_name(f'{src.name}.mdc')
        else:
            dst = Path(dest_path).resolve()
        with open(src, 'rb') as f:
            raw_bytes = f.read()
        source_size = len(raw_bytes)
        engine = LZ77Engine(search_buffer_size=search_buffer_size, lookahead_buffer_size=lookahead_buffer_size)
        triplets = engine.compress(raw_bytes, progress_callback=progress_callback)
        mdc_bytes = MDCFormat.serialize(triplets=triplets, original_data=raw_bytes, search_buffer_size=search_buffer_size, lookahead_buffer_size=lookahead_buffer_size)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, 'wb') as f:
            f.write(mdc_bytes)
        compressed_size = len(mdc_bytes)
        stats = cls.calculate_stats(source_size, compressed_size)
        return {'source_path': str(src), 'dest_path': str(dst), 'source_size': source_size, 'compressed_size': compressed_size, 'compression_ratio': stats['compression_ratio'], 'saving_percent': stats['saving_percent'], 'triplet_count': len(triplets), 'search_buffer_size': search_buffer_size, 'lookahead_buffer_size': lookahead_buffer_size}

    @classmethod
    def decompress_file(cls, source_path: str, dest_path: Optional[str]=None, progress_callback: Optional[Callable[[int, int], None]]=None) -> Dict[str, object]:
        src = Path(source_path).resolve()
        if not src.is_file():
            raise FileNotFoundError(f'Fichier archive introuvable : {source_path}')
        if dest_path is None:
            if src.suffix.lower() == '.mdc':
                candidate = src.with_suffix('')
                if candidate.exists():
                    dst = src.parent / f'{candidate.stem}_restaure{candidate.suffix}'
                else:
                    dst = candidate
            else:
                dst = src.parent / f'{src.stem}_restaure{src.suffix}'
        else:
            dst = Path(dest_path).resolve()
        with open(src, 'rb') as f:
            archive_bytes = f.read()
        header, triplets = MDCFormat.deserialize(archive_bytes)
        engine = LZ77Engine(search_buffer_size=header.search_buffer_size, lookahead_buffer_size=header.lookahead_buffer_size)
        try:
            reconstructed_bytes = engine.decompress(triplets=triplets, expected_size=header.original_size, progress_callback=progress_callback)
        except ValueError as exc:
            raise CorruptedFileError(f'Données compressées corrompues ou incohérentes : {exc}') from exc
        actual_crc = zlib.crc32(reconstructed_bytes) & 4294967295
        if actual_crc != header.original_crc32:
            raise ChecksumMismatchError(f'Échec de vérification CRC32 ! Attendu : 0x{header.original_crc32:08X}, Calculé : 0x{actual_crc:08X}. Les données décompressées sont compromises.')
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, 'wb') as f:
            f.write(reconstructed_bytes)
        return {'source_path': str(src), 'dest_path': str(dst), 'original_size': header.original_size, 'restored_size': len(reconstructed_bytes), 'crc32': f'0x{actual_crc:08X}', 'triplet_count': len(triplets), 'success': True}
