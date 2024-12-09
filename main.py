import argparse
import tkinter as tk
import os
import tarfile
from datetime import datetime
import xml.etree.ElementTree as ET


class ShellEmulator:
    def __init__(self, root, username, tar, log, script):
        self.root = root
        self.username = username
        self.tar_path = tar
        self.log_path = log
        self.script_path = script
        self.current_dir = ''
        self.file_system = self.load_tar()

        # Записываем время начала работы программы для отслеживания uptime
        self.start_time = datetime.now()

        self.root.title("Shell Emulator")
        self.text_area = tk.Text(root, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill='both')
        self.text_area.bind("<Return>", self.execute_command)
        self.text_area.focus()

        self.load_log()

        self.prompt()
        self.execute_startup_script()

    def load_tar(self):
        #Загружаем виртуальную файловую систему из архива tar.
        if not os.path.exists(self.tar_path):
            self.text_area.insert(tk.END, f"File not found: {self.tar_path}\n")
            return []
        with tarfile.open(self.tar_path, 'r') as tar:
            return [f for f in tar.getnames()]

    def load_log(self):
        #Загружаем и выводим содержимое лог-файла, если он существует.
        if os.path.exists(self.log_path):
            self.text_area.insert(tk.END, f"Loading log from: {self.log_path}\n")
            tree = ET.parse(self.log_path)
            root = tree.getroot()
            for action in root.findall("action"):
                user = action.find("user").text
                timestamp = action.find("timestamp").text
                command = action.find("command").text
                self.text_area.insert(tk.END, f"[{timestamp}] {user}: {command}\n")

    def execute_startup_script(self):
        #Выполняем команды из стартового скрипта.
        if os.path.exists(self.script_path):
            with open(self.script_path, 'r') as script_file:
                commands = script_file.readlines()
                for command in commands:
                    self.execute_command(None, command.strip())

    def prompt(self):
        #Отображаем приглашение к вводу.
        self.text_area.insert(tk.END, f"\n{self.username}@emulator:{self.current_dir}~$ ")
        self.text_area.see(tk.END)

    def log_action(self, command):
        #Логируем действие в XML-файл.
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tree = ET.ElementTree(ET.Element("log"))
        root = tree.getroot()
        action = ET.SubElement(root, "action")
        user = ET.SubElement(action, "user")
        user.text = self.username
        timestamp_elem = ET.SubElement(action, "timestamp")
        timestamp_elem.text = timestamp
        cmd = ET.SubElement(action, "command")
        cmd.text = command
        tree.write(self.log_path)

    def execute_command(self, event, command=None):
        #Обрабатываем команду пользователя.
        if not command:
            command = self.text_area.get("end-1c linestart", "end-1c").strip()
        self.text_area.insert(tk.END, '\n')  # Перевод на новую строку

        # Логируем команду
        self.log_action(command)

        cmd_parts = command.split()
        if cmd_parts:
            cmd = cmd_parts[0]
            if cmd == 'exit':
                self.root.quit()
            elif cmd == 'ls':
                self.list_files()
            elif cmd == 'cd':
                self.change_directory(cmd_parts[1] if len(cmd_parts) > 1 else '')
            elif cmd == 'uptime':
                self.show_uptime()
            elif cmd == 'uniq':
                if len(cmd_parts) > 1:
                    self.show_uniq(cmd_parts[1])
                else:
                    self.text_area.insert(tk.END, "uniq requires a filename argument\n")
            elif cmd == 'chown':
                if len(cmd_parts) > 2:
                    self.change_owner(cmd_parts[1], cmd_parts[2])
                else:
                    self.text_area.insert(tk.END, "chown requires user and file arguments\n")
            else:
                self.text_area.insert(tk.END, f"Unknown command: {cmd}\n")
        self.prompt()

    def list_files(self):
        #Выводим список файлов в текущей директории.
        current_files = [f for f in self.file_system if f.startswith(self.current_dir)]
        if current_files:
            for file in current_files:
                self.text_area.insert(tk.END, f"{file[len(self.current_dir):]}  \n")
        else:
            self.text_area.insert(tk.END, "No files found\n")

    def change_directory(self, directory):
        #Изменяем текущую директорию.
        if directory == '..':
            self.current_dir = '/'.join(self.current_dir.split('/')[:-1]) + '/' if self.current_dir != '' else ''
        else:
            full_path = self.current_dir + directory
            if full_path in self.file_system:
                self.current_dir = full_path + '/'
            else:
                self.text_area.insert(tk.END, f"No such directory: {directory}\n")

    def show_uptime(self):
        #Показываем uptime (в данной версии просто выводим время работы программы).
        uptime = datetime.now() - self.start_time
        self.text_area.insert(tk.END, f"Uptime: {uptime}\n")

    def show_uniq(self, filename):
        #Показываем уникальные строки в файле.
        full_path = self.current_dir + filename
        if full_path in self.file_system:
            with tarfile.open(self.tar_path, 'r') as tar:
                try:
                    file_member = tar.getmember(full_path)
                    if file_member.isfile():
                        with tar.extractfile(file_member) as f:
                            content = f.read().decode('utf-8').splitlines()
                            unique_lines = set(content)
                            self.text_area.insert(tk.END, "\n".join(unique_lines) + "\n")
                    else:
                        self.text_area.insert(tk.END, f"{filename} is not a file\n")
                except KeyError:
                    self.text_area.insert(tk.END, f"No such file: {filename}\n")
        else:
            self.text_area.insert(tk.END, f"No such file: {filename}\n")

    def change_owner(self, user, filename):
        self.text_area.insert(tk.END, f"Changed owner of {filename} to {user}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shell Emulator")
    parser.add_argument("--username", required=False, default="Alexey", help="Username")
    parser.add_argument("--tar", required=False, default="C:\\Users\\Алексей\\PycharmProjects\\config_1\\tests.tar", help="Путь к архиву tar")
    parser.add_argument("--log", required=False, default="C:\\Users\\Алексей\\PycharmProjects\\config_1\\logs\\log.xml", help="Путь к лог файлу")
    parser.add_argument("--script", required=False, default="C:\\Users\\Алексей\\PycharmProjects\\config_1\\scripts\\startup1.sh", help="Путь к стартовому скрипту")
    args = parser.parse_args()

    root = tk.Tk()
    emulator = ShellEmulator(root, args.username, args.tar, args.log, args.script)
    root.mainloop()