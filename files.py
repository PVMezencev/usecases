import os


def get_files_from_fs(root: str) -> list:
    """
    Вернёт пути ко всем файлам, в том числе из вложенных папок.
    :param root: начальная директория поиска
    :return: список путей
    """
    files_list = list()

    for f in os.listdir(root):
        f_abs = os.path.join(root, f)
        if os.path.isfile(f_abs):
            files_list.append(f_abs)
        elif os.path.isdir(f_abs):
            files_list += get_files_from_fs(f_abs)

    return files_list
  
  # Пример получения всех типов (расширений) файлов из заданой папки.
start_dir = '/home/user/_orders/'

all_files = get_files_from_fs(start_dir)

# Заготовка для списка типов.
all_ext = list()

for f in all_files:
    if os.path.isfile(f):
        # Разделяем путь файла по точкам.
        parts = str(f).split('.')
        # Берём последний элемент после точки.
        ext = parts[-1]
        # Собираем расширения в строчном регистре.
        all_ext.append(ext.lower())

# Унифицируем список полученных типов: переведём список во множество, так как оно не может содержать повторяющихся
# элементов, затем обратно в список.
all_ext = list(set(all_ext))

# Вывод в stdout.
print(f'В папке "{start_dir}" содержатся файлы следующих типов: {", ".join(all_ext)}')
