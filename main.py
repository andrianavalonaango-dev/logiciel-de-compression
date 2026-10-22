import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from madacompress.cli import main_cli

def main():
    try:
        sys.exit(main_cli(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\n[!] Opération interrompue par l'utilisateur.")
        sys.exit(130)
if __name__ == '__main__':
    main()
