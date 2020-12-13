# GitHub: @howtus
import os
from datetime import datetime
from pathlib import Path
import requests
import dateutil.parser as dparser

# Задаем константы для ссылок на API.
URL_TODOS = "https://json.medrating.org/todos"
URL_USERS = "https://json.medrating.org/users"


# Функция получения и парсинга JSON в словарь.
def get_json(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print('Ошибка подключения. Проверьте корректность URL.')
        raise SystemExit(e)
    except requests.exceptions.ConnectionError as e:
        print('Ошибка подключения. Проверьте Интернет-соединение.')
        raise SystemExit(e)
    except requests.exceptions.Timeout as e:
        print('Превышено время ожидания ответа сервера.')
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        print('Ошибка при подключении к серверу.')
        raise SystemExit(e)
    return response.json()


# Функция для обрезки строк и добавления многоточия.
def truncate_str(str):
    if len(str) > 48:
        return str[:48] + '...\n'
    return str + '\n'


# Функция для переименования старого файла пользователя.
# Возвращает False, если возникла ошибка при чтении файла.
# Второе значение - путь к переименованному файлу.
# Нужен, если вдруг возникнет ошибка записи в новый файл.
def rename_file(username):
    # Записываем путь до файла.
    path = 'tasks/' + username + '.txt'
    try:
        with open(path) as file:
            # Достаем дату из файла и преобразуем ее в другой формат.
            date = dparser.parse(file.readlines()[1].split('> ')[1], fuzzy=True).isoformat()
    except:
        print('Возникла ошибка при чтении файла для переименования.')
        return (False, '')
    # Переименовываем файл.
    new_path = 'tasks/old_' + username + '_' + date + '.txt'
    os.rename(path, new_path)
    return (True, new_path)


# Функция для создания актуального файла пользователя.
def make_file(user_id, data_users, data_todos, old_file):
    # Списки для задач пользователя
    tasks = []
    completed_tasks = []

    # Считаем задачи пользователя и записываем их в списки.
    print('Парсим задачи пользователя...')
    for task in data_todos:
        if task.get('userId') == user_id:
            if task.get('completed'):
                completed_tasks.append(truncate_str(task.get('title')))
            else:
                tasks.append(truncate_str(task.get('title')))

    # Считываем данные пользователя
    username = ''
    file_header = 'Отчёт для '
    print('Парсим данные пользователя...')
    for user in data_users:
        if user.get('id') == user_id:
            username = user.get('username')
            # Костыль, чтобы сократить количество записей на диск.
            file_header += f"{user.get('company').get('name')}.\n" \
                           f"{user.get('name')} <{user.get('email')}> " \
                           f"{datetime.now().strftime('%d.%m.%Y %H:%M')}\n" \
                           f"Всего задач: {str(len(completed_tasks) + len(tasks))}\n\n"
            # Проверяем крайний случай
            if not len(completed_tasks):
                file_header += "Нет завершенных задач.\n"
            else:
                file_header += f"Завершённые задачи ({str(len(completed_tasks))}):\n"
                file_header += ''.join(completed_tasks)
            if not len(tasks):
                file_header += "\nНет оставшихся задач."
            else:
                file_header += f"\nОставшиеся задачи ({str(len(tasks))}):\n"
                file_header += ''.join(tasks)

    # Записываем все данные в файл
    print('Записываем данные в файл...')
    try:
        with open('tasks/' + username + '.txt', 'w+') as file:
            file.write(file_header)
    except:
        # При возникновении ошибки удаляем файл
        print('Возникла ошибка при записи в файл.')
        print('Файл будет удален.')
        if os.path.isfile('tasks/' + username + '.txt'):
            os.remove('tasks/' + username + '.txt')
        if not old_file:
            print('Восстанавливаем старый файл.')
            os.rename(old_file, 'tasks/' + username + '.txt')


def main():
    print('### Запуск скрипта ###')
    # Создаем папку, если её еще не существует.
    Path('tasks').mkdir(parents=True, exist_ok=True)
    # Отправляем запрос на сервер для получения данных в формате JSON.
    print('Загружаем данные с сервера...')
    data_users = get_json(URL_USERS)
    data_todos = get_json(URL_TODOS)
    # Проходимся по массиву пользователей.
    print('Создаем файлы...')
    for user in data_users:
        # Т.к. часто встречаются пустые пользователи, то проверяем наличие username у них.
        if user.get('username'):
            # Если файл уже существует, то переименовываем его.
            if os.path.isfile('tasks/' + user.get('username') + '.txt'):
                print('Переименовываем старый файл ' + user.get('username') + '...')
                read_errors, old_file_path = rename_file(user.get('username'))
                # Если функция вернула False, значит есть ошибка чтения.
                # Идем к следующей итерации цикла, чтобы не создавать новый файл.
                if not read_errors:
                    print('Пропускаем данный файл.')
                    continue
            else:
                old_file_path = ''
            # Создаем новый файл.
            print('Создаем актуальный файл для ' + user.get('username') + '...')
            make_file(user.get('id'), data_users, data_todos, old_file_path)
    print('### Конец работы скрипта ###')


if __name__ == "__main__":
    main()
