import logging
from prettytable import PrettyTable
from constants import BASE_DIR, DATETIME_FORMAT
import datetime as dt
import csv


def control_output(results: list, cli_args):
    """
    Функция обработчик для вывода ответа
    в выбранном формате.
    """
    output = cli_args.output

    if output == 'pretty':
        pretty_output(results)

    elif output == 'file':
        file_output(results, cli_args)

    else:
        default_output(results)


def default_output(results: list):
    """
    Построчный вывод.
    """
    for row in results:
        print(*row)


def pretty_output(results: list):
    """
    Вывод в табличном виде.
    """
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'

    table.add_rows(results[1:])
    print(table)


def file_output(results: list, cli_args):
    """
    Вывод в csv.
    """
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)

    parser_mode = cli_args.mode
    date_now = dt.datetime.now()
    now_format = date_now.strftime(DATETIME_FORMAT)

    file_name = f'{parser_mode}_{now_format}.csv'
    file_path = results_dir / file_name

    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect='unix')
        writer.writerows(results)

    logging.info(f'Файл с результатами был сохранён: {file_path}')
