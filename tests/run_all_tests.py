import sys
import time
import unittest
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def run_tests():
    print('=' * 70)
    print('       SUITE DE TESTS AUTOMATISÉS — MADACOMPRESS (LZ77)')
    print('=' * 70)
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(PROJECT_ROOT / 'tests'), pattern='test_*.py')
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time
    print('\n' + '=' * 70)
    print('                      RÉSUMÉ DE LA VALIDATION')
    print('=' * 70)
    print(f'Tests exécutés : {result.testsRun}')
    print(f'Succès         : {result.testsRun - len(result.failures) - len(result.errors)}')
    print(f'Échecs         : {len(result.failures)}')
    print(f'Erreurs        : {len(result.errors)}')
    print(f'Temps écoulé   : {duration:.3f} secondes')
    print('=' * 70)
    if result.wasSuccessful():
        print('>>> TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS (100% SUCCÈS) <<<')
        return 0
    else:
        print('>>> ÉCHEC DE CERTAINS TESTS <<<')
        return 1
if __name__ == '__main__':
    sys.exit(run_tests())
