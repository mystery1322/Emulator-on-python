import tkinter as tk
import os

def process_command():
    command = entry.get().strip()
    entry.delete(0, tk.END)  # Очищаем поле ввода

    # Разбиваем команду на части и обрабатываем переменные окружения
    parts = []
    for part in command.split():
        if part.startswith('$'):
            # Заменяем переменные окружения
            var_name = part[1:]
            parts.append(os.environ.get(var_name, part))
        else:
            parts.append(part)

    if not parts:  # Если команда пустая
        output = ""
    else:
        cmd = parts[0]
        args = parts[1:]

    match cmd:
        case "ls":
            output = f"ls called with args: {args}\n"
        case "cd":
            output = f"cd called with args: {args}\n"
        case "exit":
            root.destroy()
            return
        case _:
            output = f"Error: unknown command '{cmd}'\n"

    # Добавляем вывод в текстовое поле
    text.config(state=tk.NORMAL)
    text.insert(tk.END, f"VFS> {command}\n")  # Показываем введенную команду
    text.insert(tk.END, output)  # Показываем результат
    text.see(tk.END)  # Прокручиваем к концу
    text.config(state=tk.DISABLED)

# Создаем главное окно
root = tk.Tk()
root.title("Эмулятор - VFS")  # Заголовок с именем VFS

# Создаем текстовое поле для вывода
text = tk.Text(root, bg="black", fg="white", state=tk.DISABLED)
text.pack(expand=True, fill=tk.BOTH)

# Создаем рамку для поля ввода и кнопки
frame = tk.Frame(root)
frame.pack(fill=tk.X)

# Создаем поле для ввода команд
entry = tk.Entry(frame, bg="black", fg="white", insertbackground="white")
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
entry.bind("<Return>", lambda event: process_command())  # Обработка нажатия Enter

# Создаем кнопку для выполнения команды
button = tk.Button(frame, text="Run", command=process_command)
button.pack(side=tk.RIGHT, padx=5, pady=5)

# Фокусируемся на поле ввода
entry.focus()
root.mainloop()