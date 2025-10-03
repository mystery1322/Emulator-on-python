import tkinter as tk
import os
import argparse
from typing import List

# Здесь мы храним значение --vfs-path
current_vfs_path: str | None = None


# Анализ аргументов командной строки
def parse_cli_args():

    parser = argparse.ArgumentParser(
        description="Emulator - Stage 2 (configuration). Stubs for cd/ls, startup script playback."
    )
    parser.add_argument("--vfs-path", "-v", help="Path to physical VFS location (for debugging)", default=None)
    parser.add_argument("--startup-script", "-s", help="Path to startup script (lines, '#' comments)", default=None)
    return parser.parse_args()

def expand_args(args: List[str]) -> List[str]:

    #Разворачивает переменные окружения и символ ~ в каждом аргументе.
    result: List[str] = []
    for a in args:
        if a is None or a == "":
            result.append(a)
            continue
        # Сначала разворачиваем переменные окружения ($VAR или %VAR%), затем ~
        expanded = os.path.expandvars(a)
        expanded = os.path.expanduser(expanded)
        result.append(expanded)
    return result


# Основная обработка команд (заглушки)
def handle_command_internals(command: str) -> str:
    parts = command.strip().split()
    if not parts:
        return ""  # пустая строка — ничего не выводим

    cmd = parts[0]
    args = parts[1:]

    # Используем match/case для краткости и читабельности
    match cmd:
        case "echo":
            expanded = expand_args(args)
            # Возвращаем одну строку, добавляем перевод строки в конце
            return " ".join(expanded) + "\n"

        case "ls":
            # Заглушка: показываем какие аргументы были переданы.
            return f"ls called with args: {args}\n"

        case "cd":
            # (не меняем current_vfs_path здесь — т.к. это заглушка)
            return f"cd called with args: {args}\n"

        case "exit":
            try:
                root.destroy()
            except NameError:
                # Если root не задан — просто ничего не делаем
                pass
            return ""
        case _:
            # Неизвестная команда — возвращаем понятную ошибку
            return f"Error: unknown command '{cmd}'\n"


# Работа с виджетом — безопасная вставка текста
def insert_text(text_widget: tk.Text, s: str) -> None:
    """
    Вставляет строку s в text_widget в состоянии read-only (мы временно включаем запись).
    Поддерживает автопрокрутку вниз.
    """
    text_widget.config(state=tk.NORMAL)  # включаем запись
    text_widget.insert(tk.END, s)  # вставляем текст
    text_widget.see(tk.END)  # прокручиваем к концу
    text_widget.config(state=tk.DISABLED)  # снова делаем read-only

# Выполнение одной команды (показ ввода + вывод)
def execute_command_line(command: str, show_input: bool = True) -> str:

    #Выполняет одну строку команды: показывает 'ввод' (VFS> ...) и затем вывод (результат).

    if show_input:
        insert_text(text, f"VFS> {command}\n")
    output = handle_command_internals(command)
    if output:
        insert_text(text, output)
    return output

# Обработка ввода из поля Entry (по Enter или кнопке Run)
def process_command_from_entry() -> None:
    """
    Берёт текст из поля ввода (entry), очищает поле и выполняет команду.
    Используется как callback для нажатия Enter и для кнопки 'Run'.
    """
    command = entry.get().strip()
    entry.delete(0, tk.END)
    execute_command_line(command)

# Проигрывание стартового скрипта построчно (имитация диалога)
def run_startup_script_lines(lines: List[str]) -> None:

    #Проигрывает список строк start-up скрипта, имитируя диалог:

    delay_ms = 200
    scheduled_index = 0
    for raw in lines:
        line = raw.rstrip("\n")
        # Пропускаем пустые строки и комментарии (комментарий — строка, начинающаяся с '#')
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        # Планируем выполнение конкретной строки с задержкой
        root.after(delay_ms * scheduled_index, lambda cmd=line: execute_command_line(cmd, show_input=True))
        scheduled_index += 1

# Загрузка и запуск стартового скрипта (файла)
def load_and_run_startup_script(path: str) -> None:

    if not os.path.isfile(path):
        insert_text(text, f"Startup script not found: {path}\n")
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        insert_text(text, f"Failed to read startup script {path}: {e}\n")
        return

    insert_text(text, f"# running startup script: {path}\n")
    run_startup_script_lines(lines)

# MAIN — инициализация GUI и запуск
args = parse_cli_args()
current_vfs_path = args.vfs_path  # просто сохраняем для отладочного вывода

# Создаём окно и виджеты
root = tk.Tk()
root.title("Эмулятор - VFS (конфиг)")

# Основное текстовое поле — в режиме только для чтения (мы временно включаем запись при вставке)
text = tk.Text(root, bg="black", fg="white", state=tk.DISABLED)
text.pack(expand=True, fill=tk.BOTH)

# Поле ввода + кнопка
frame = tk.Frame(root)
frame.pack(fill=tk.X)

entry = tk.Entry(frame, bg="black", fg="white", insertbackground="white")
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
entry.bind("<Return>", lambda event: process_command_from_entry())  # Enter вызывает выполнение

button = tk.Button(frame, text="Run", command=process_command_from_entry)
button.pack(side=tk.RIGHT, padx=5, pady=5)

entry.focus()

# При старте выводим отладочную информацию о параметрах (требование этапа)
insert_text(text, f"Startup parameters:\n  vfs-path: {args.vfs_path}\n  startup-script: {args.startup_script}\n\n")

# Если задан стартовый скрипт — запустим его через небольшую задержку,
if args.startup_script:
    root.after(100, lambda: load_and_run_startup_script(args.startup_script))

# Запуск основного цикла Tkinter (блокирующая функция)
root.mainloop()
