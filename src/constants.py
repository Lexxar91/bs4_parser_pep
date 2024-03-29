from pathlib import Path

MAIN_DOC_URL = 'https://docs.python.org/3/'
BASE_DIR = Path(__file__).parent
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}

PEP_URL = 'https://peps.python.org/'
RESULTS = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор',)]
RESULTS_VERSIONS = [('Ссылка на документацию', 'Версия', 'Статус')]
RESULTS_PEP = [('Статус', 'Количество',)]
