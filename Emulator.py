#!/usr/bin/env python3

import tkinter as tk
import os
import argparse
import sys

current_vfs_path = None  # глобальная "виртуальная" рабочая директория (строка или None)

def expand_args(args):
    """Расширяет переменные окружения вида $VAR и ~ в списке аргументов."""
    expanded = []
    for a in args:
        if not a:
            expanded.append(a)
            continue
        a = os.path.expanduser(os.path.expandvars(a))
        expanded.append(a)
    return expanded

def _resolve_target_path(target):
    """
    Привести target (строка) к абсолютному нормализованному пути.
    Если target относительный и current_vfs_path задан — сделать путь относительно current_vfs_path.
    """
    if not target:
        return None
    # уже расширили переменные в caller, но на всякий случай:
    target = os.path.expanduser(os.path.expandvars(target))
    target = os.path.normpath(target)
    if not os.path.isabs(target):
        base = current_vfs_path or os.getcwd()
        target = os.path.normpath(os.path.join(base, target))
    # окончательно абсолютный:
    target = os.path.abspath(target)
    return target

def handle_command_internals(command):
    """
    Обрабатывает команду (строку) и возвращает текст-вывода.
    Поддерживаемые команды: echo, ls, cd, mkdir, exit.
    """
    global current_vfs_path
    parts = command.strip().split()
    if not parts:
        return ""
    cmd = parts[0]
    args = parts[1:]

    if cmd == "echo":
        args = expand_args(args)
        return " ".join(args) + "\n"

    elif cmd == "ls":
        # если аргумент есть — используем его, иначе текущий vfs-path или cwd
        if args:
            arg = args[0]
            target = _resolve_target_path(arg)
        else:
            target = current_vfs_path or os.getcwd()
        if not target:
            target = os.getcwd()
        if not os.path.exists(target):
            return f"ls: path not found: {target}\n"
        if os.path.isdir(target):
            try:
                names = os.listdir(target)
                if not names:
                    return "(empty)\n"
                return "  ".join(names) + "\n"
            except Exception as e:
                return f"ls error: {e}\n"
        else:
            # если это файл — вернуть имя файла
            return f"{os.path.basename(target)}\n"

    elif cmd == "cd":
        if not args:
            return "cd: missing argument\n"
        candidate = args[0]
        new_path = _resolve_target_path(candidate)
        if not os.path.exists(new_path):
            return f"cd: no such file or directory: {new_path}\n"
        if not os.path.isdir(new_path):
            return f"cd: not a directory: {new_path}\n"
        current_vfs_path = new_path
        return f"changed vfs path to: {current_vfs_path}\n"

    elif cmd == "mkdir":
        if not args:
            return "mkdir: missing directory name\n"
        name = args[0]
        target = _resolve_target_path(name)
        try:
            os.makedirs(target, exist_ok=True)
            return f"mkdir: created {target}\n"
        except Exception as e:
            return f"mkdir error: {e}\n"

    elif cmd == "exit":
        try:
            root.destroy()
        except NameError:
            pass
        return ""

    else:
        return f"Error: unknown command '{cmd}'\n"

def insert_text(text_widget, s):
    text_widget.config(state=tk.NORMAL)
    text_widget.insert(tk.END, s)
    text_widget.see(tk.END)
    text_widget.config(state=tk.DISABLED)

def execute_command_line(command, show_input=True):
    if show_input:
        insert_text(text, f"VFS> {command}\n")
    output = handle_command_internals(command)
    if output:
        insert_text(text, output)
    return output

def process_command_from_entry():
    command = entry.get().strip()
    entry.delete(0, tk.END)
    execute_command_line(command)

def run_startup_script_lines(lines):
    delay = 200  # ms между строками
    scheduled_index = 0
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        # захватываем текущее значение line через default-аргумент
        root.after(delay * scheduled_index, lambda cmd=line: execute_command_line(cmd, show_input=True))
        scheduled_index += 1

def load_and_run_startup_script(path):
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

def parse_cli_args():
    parser = argparse.ArgumentParser(description="Emulator - VFS (GUI) with startup script support")
    parser.add_argument("--vfs-path", "-v", help="Path to physical VFS location", default=None)
    parser.add_argument("--startup-script", "-s", help="Path to startup script (lines, '#' comments)", default=None)
    return parser.parse_args()

# ---------- MAIN ----------
args = parse_cli_args()

# Нормализуем и приводим vfs-path к абсолютному пути, если он задан
if args.vfs_path:
    resolved = os.path.expanduser(os.path.expandvars(args.vfs_path))
    resolved = os.path.normpath(resolved)
    resolved = os.path.abspath(resolved)
    current_vfs_path = resolved
else:
    current_vfs_path = None

root = tk.Tk()
root.title("Эмулятор - VFS (конфиг)")

text = tk.Text(root, bg="black", fg="white", state=tk.DISABLED)
text.pack(expand=True, fill=tk.BOTH)

frame = tk.Frame(root)
frame.pack(fill=tk.X)

entry = tk.Entry(frame, bg="black", fg="white", insertbackground="white")
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
entry.bind("<Return>", lambda event: process_command_from_entry())

button = tk.Button(frame, text="Run", command=process_command_from_entry)
button.pack(side=tk.RIGHT, padx=5, pady=5)

entry.focus()

insert_text(text, f"Startup parameters:\n  vfs-path: {current_vfs_path}\n  startup-script: {args.startup_script}\n\n")

if args.startup_script:
    root.after(100, lambda: load_and_run_startup_script(args.startup_script))

root.mainloop()
