import unittest
import tkinter as tk
import os
import tarfile
import tempfile
from main import ShellEmulator
from datetime import datetime, timedelta


class TestEmulator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tar_path = os.path.join(self.temp_dir.name, "tests.tar")
        self.log_path = os.path.join(self.temp_dir.name, "log.xml")
        self.script_path = os.path.join(self.temp_dir.name, "startup.sh")

        # Создаем тестовый tar-архив
        with tarfile.open(self.tar_path, "w") as tar:
            folders = {
                "tests/chown_test": ["file1.txt", "file2.txt"],
                "tests/uniq_test": ["data1.txt", "data2.txt"],
            }
            for folder, files in folders.items():
                folder_path = os.path.join(self.temp_dir.name, folder)
                os.makedirs(folder_path)
                for file in files:
                    file_path = os.path.join(folder_path, file)
                    with open(file_path, "w", encoding="utf-8") as f:
                        if "data1" in file:
                            f.write("line1\nline2\nline1\nline3\n")
                        if "data2" in file:
                            f.write("unique\nunique\ntext\ntext\n")
                    tar.add(file_path, arcname=f"{folder}/{file}")

        # Создаем пустой лог-файл
        with open(self.log_path, "w", encoding="utf-8") as log_file:
            log_file.write("<log></log>")

        # Создаем скрипт
        with open(self.script_path, "w", encoding="utf-8") as script_file:
            script_file.write("ls\ncd chown_test\nexit\n")

        # Настраиваем ShellEmulator
        self.root = tk.Tk()
        self.emulator = ShellEmulator(self.root, "Alexey", self.tar_path, self.log_path, self.script_path)
        self.emulator.text_area.delete("1.0", tk.END)  # Очищаем текстовую область

    def tearDown(self):
        self.temp_dir.cleanup()
        self.root.destroy()

    # Тесты для uptime
    def test_uptime_initial(self):
        self.emulator.start_time = datetime.now() - timedelta(seconds=0)
        self.emulator.execute_command(None, "uptime")
        output = self.emulator.text_area.get("1.0", tk.END).strip()
        self.assertIn("Uptime: 0:00:00", output)

    def test_uptime_after_delay(self):
        self.emulator.start_time = datetime.now() - timedelta(seconds=90)
        self.emulator.execute_command(None, "uptime")
        output = self.emulator.text_area.get("1.0", tk.END).strip()
        self.assertIn("Uptime: 0:01:30", output)

    # Тест для команды exit
    def test_exit(self):
        self.emulator.execute_command(None)  # вызываем команду выхода
        self.assertTrue(self.root.winfo_exists())  # проверяем, открыто ли окно

    # Тесты для cd
    def test_cd_1(self):
        self.emulator.change_directory("non_existing_dir")
        output = self.emulator.text_area.get("1.0", tk.END).strip()
        self.assertIn("No such directory: non_existing_dir", output)

    def test_cd_2(self):
        self.emulator.change_directory("non_existing_dir")
        output = self.emulator.text_area.get("1.0", tk.END).strip()
        self.assertIn("No such directory: non_existing_dir", output)

    # Тесты для ls
    def test_ls_1(self):
        self.emulator.current_dir = "tests/chown_test/"
        self.emulator.list_files()
        output = self.emulator.text_area.get("1.0", tk.END)
        self.assertIn("file1.txt", output)
        self.assertIn("file2.txt", output)

    def test_ls_2(self):
        self.emulator.current_dir = "non_existing_dir/"
        self.emulator.list_files()
        output = self.emulator.text_area.get("1.0", tk.END)
        self.assertIn("No files found", output)

    # Тесты для chown
    def test_chown_1(self):
        self.emulator.current_dir = "tests/chown_test/"
        self.emulator.change_owner("Alexey", "file1.txt")
        output = self.emulator.text_area.get("1.0", tk.END).strip()
        self.assertIn("Changed owner of file1.txt to Alexey", output)

    def test_chown_2(self):
        self.emulator.current_dir = "tests/chown_test/"
        self.emulator.change_owner("Vlad", "file2.txt")
        output = self.emulator.text_area.get("1.0", tk.END).strip()
        self.assertIn("Changed owner of file2.txt to Vlad", output)

    # Тесты для uniq
    def test_uniq_1(self):
        self.emulator.current_dir = "tests/uniq_test/"
        self.emulator.show_uniq("data1.txt")
        output = self.emulator.text_area.get("1.0", tk.END)
        self.assertIn("line1", output)
        self.assertIn("line2", output)
        self.assertIn("line3", output)

    def test_uniq_2(self):
        self.emulator.current_dir = "tests/uniq_test/"
        self.emulator.show_uniq("data2.txt")
        output = self.emulator.text_area.get("1.0", tk.END)
        self.assertIn("unique", output)
        self.assertIn("text", output)


if __name__ == "__main__":
    unittest.main()
