import argparse
import sys
from pathlib import Path
from typing import List, Optional
from .engine.lz77 import LZ77Engine
from .format.file_manager import FileManager
from .format.mdc_format import MDCError

def format_size(bytes_count: int) -> str:
    for unit in ['octets', 'Ko', 'Mo', 'Go']:
        if bytes_count < 1024.0:
            return f'{bytes_count:.2f} {unit}' if unit != 'octets' else f'{bytes_count} {unit}'
        bytes_count /= 1024.0
    return f'{bytes_count:.2f} To'

def run_pedagogical_demo_cli(text: str='CABRACADABRARRARRAD', search_size: int=LZ77Engine.COURSE_SEARCH_SIZE, lookahead_size: int=LZ77Engine.COURSE_LOOKAHEAD_SIZE) -> None:
    engine = LZ77Engine(search_buffer_size=search_size, lookahead_buffer_size=lookahead_size)
    print('=' * 80)
    print('        DÉMONSTRATION PÉDAGOGIQUE LZ77 — MADACOMPRESS')
    print('=' * 80)
    print(f"Texte d'entrée            : {text}")
    print(f'Longueur du texte         : {len(text)} caractères')
    print(f'Taille tampon recherche   : {search_size}')
    print(f'Taille tampon anticipation: {lookahead_size}')
    print('-' * 80)
    print(f'{'Étape':<6} | {'Tampon Recherche':<18} | {'Tampon Entrée':<15} | {'Triplet':<12} | {'Décodé'}')
    print('-' * 80)
    steps = list(engine.step_by_step_encode(text))
    for s in steps:
        sb_display = f'[{s['search_buffer']:>{search_size}}]'
        lb_display = f'[{s['lookahead_buffer']:<{lookahead_size}}]'
        triplet_str = str(s['triplet'])
        print(f'{s['step']:<6} | {sb_display:<18} | {lb_display:<15} | {triplet_str:<12} | {s['decoded_so_far']}')
    print('-' * 80)
    print('Vérification du décodage final :')
    decoded = engine.decompress_text([s['triplet'] for s in steps])
    if decoded == text:
        print(f"SUCCÈS : Le texte reconstruit correspond à 100% : '{decoded}'")
    else:
        print(f"ERREUR : Désaccord de décodage ! Reconstruit : '{decoded}'")
    print('=' * 80)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='MadaCompress', description='MadaCompress — Logiciel universitaire de compression et décompression LZ77.', formatter_class=argparse.RawDescriptionHelpFormatter, epilog="\nExemples d'utilisation :\n  python main.py --compress -i document.txt -o document.txt.mdc\n  python main.py --decompress -i document.txt.mdc -o document_restaure.txt\n  python main.py --demo CABRACADABRARRARRAD\n  python main.py --gui\n")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-c', '--compress', action='store_true', help='Compresser le fichier source en archive propriétaire .mdc')
    mode_group.add_argument('-d', '--decompress', action='store_true', help='Décompresser un fichier .mdc')
    mode_group.add_argument('--demo', nargs='?', const='CABRACADABRARRARRAD', metavar='TEXTE', help='Lancer la démonstration pédagogique pas-à-pas (défaut: texte du cours)')
    mode_group.add_argument('-g', '--gui', action='store_true', help="Lancer l'interface graphique utilisateur (GUI)")
    parser.add_argument('-i', '--input', metavar='FICHIER', help="Chemin du fichier d'entrée (source)")
    parser.add_argument('-o', '--output', metavar='FICHIER', help='Chemin du fichier de sortie (destination)')
    parser.add_argument('-s', '--search-size', type=int, default=LZ77Engine.DEFAULT_SEARCH_SIZE, metavar='OCTETS', help=f'Taille du tampon de recherche en octets (défaut: {LZ77Engine.DEFAULT_SEARCH_SIZE})')
    parser.add_argument('-l', '--lookahead-size', type=int, default=LZ77Engine.DEFAULT_LOOKAHEAD_SIZE, metavar='OCTETS', help=f"Taille du tampon d'anticipation en octets (défaut: {LZ77Engine.DEFAULT_LOOKAHEAD_SIZE})")
    return parser

def main_cli(args: Optional[List[str]]=None) -> int:
    parser = build_parser()
    parsed_args = parser.parse_args(args)
    if parsed_args.gui or (not parsed_args.compress and (not parsed_args.decompress) and (parsed_args.demo is None) and (not parsed_args.input)):
        from .gui.app import launch_gui
        launch_gui()
        return 0
    if parsed_args.demo is not None:
        run_pedagogical_demo_cli(text=parsed_args.demo, search_size=parsed_args.search_size if parsed_args.search_size != LZ77Engine.DEFAULT_SEARCH_SIZE else LZ77Engine.COURSE_SEARCH_SIZE, lookahead_size=parsed_args.lookahead_size if parsed_args.lookahead_size != LZ77Engine.DEFAULT_LOOKAHEAD_SIZE else LZ77Engine.COURSE_LOOKAHEAD_SIZE)
        return 0
    if parsed_args.compress:
        if not parsed_args.input:
            print("Erreur : veuillez spécifier le fichier d'entrée avec -i / --input", file=sys.stderr)
            return 1
        print(f'[*] Compression de : {parsed_args.input}')
        try:
            stats = FileManager.compress_file(source_path=parsed_args.input, dest_path=parsed_args.output, search_buffer_size=parsed_args.search_size, lookahead_buffer_size=parsed_args.lookahead_size)
            print('[+] Compression terminée avec succès !')
            print(f'    - Fichier compressé : {stats['dest_path']}')
            print(f'    - Taille originale  : {format_size(stats['source_size'])}')
            print(f'    - Taille compressée : {format_size(stats['compressed_size'])}')
            print(f'    - Taux de compression : {stats['compression_ratio']:.4f}')
            print(f"    - Gain d'espace       : {stats['saving_percent']}%")
            print(f'    - Nombre de triplets  : {stats['triplet_count']}')
            return 0
        except (FileNotFoundError, MDCError, Exception) as exc:
            print(f'[-] Échec de compression : {exc}', file=sys.stderr)
            return 1
    if parsed_args.decompress:
        if not parsed_args.input:
            print("Erreur : veuillez spécifier le fichier archive d'entrée avec -i / --input", file=sys.stderr)
            return 1
        print(f'[*] Décompression de : {parsed_args.input}')
        try:
            stats = FileManager.decompress_file(source_path=parsed_args.input, dest_path=parsed_args.output)
            print('[+] Décompression terminée avec succès !')
            print(f'    - Fichier restauré : {stats['dest_path']}')
            print(f'    - Taille restaurée : {format_size(stats['restored_size'])}')
            print(f'    - Contrôle CRC32   : {stats['crc32']} (Intégrité vérifiée)')
            return 0
        except (FileNotFoundError, MDCError, Exception) as exc:
            print(f'[-] Échec de décompression : {exc}', file=sys.stderr)
            return 1
    parser.print_help()
    return 0
