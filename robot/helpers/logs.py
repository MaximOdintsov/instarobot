import sys
import os
import traceback
from functools import wraps
from datetime import datetime, date
from robot import config


def capture_output_to_file(command_name: str):
    """
    Декоратор, который перенаправляет stdout и stderr в файлы:
      data/logs/<command_name>.out
      data/logs/<command_name>.err

    - Каждая "законченная" строка (с '\n') получает таймштамп только один раз.
    - Если внутри команды случится исключение:
        - Печатаем traceback в .err (с таймштампом только на первом "Traceback"),
          остальные строки traceback идут без префикса.
        - Выходим через sys.exit(1), чтобы Click не добавлял второй traceback.
    """

    class Tee:
        """
        Заменяем io.TextIOWrapper на более гибкий класс:

        1. Собираем куски вывода построчно, чтобы не склеивались таймштампы в середине.
        2. Если увидели "Traceback (most recent call last):", включаем режим traceback,
           и дальше печатаем строки без префикса, пока traceback не закончится
           (или до следующего принта, если хотим логику усложнить).
        """
        def __init__(self, real_stream, log_file, is_err=False):
            """
            :param real_stream: исходный sys.stdout или sys.stderr
            :param log_file: файловый объект (открытый на append)
            :param is_err: True, если это stderr (для отслеживания traceback)
            """
            self.real_stream = real_stream
            self.log_file = log_file
            self.is_err = is_err

            # Здесь будем накапливать куски, когда нет \n
            self.buffer = ""

            # Флаг, указывающий, что мы «внутри traceback»
            self.in_traceback = False

        def write(self, s):
            if not s:
                return

            # Накапливаем всё во временном буфере
            self.buffer += s

            # Разбиваем буфер по строкам (сохраняя '\n')
            lines = self.buffer.split('\n')

            # Последняя часть может быть без '\n' (т.е. "недоделанная" строка),
            # поэтому оставим её в self.buffer, а всё остальное считаем "готовыми" строками
            self.buffer = lines.pop()  # это хвост, без \n

            # Обрабатываем все "законченные" строки
            for line in lines:
                self._write_line(line + '\n')  # line уже без \n, а мы добавим обратно

        def flush(self):
            """
            Вызывается системой для "выдавливания" буфера.
            У нас часть строки может лежать в self.buffer без \n.
            Если хотим, чтобы при flush это тоже записывалось с таймштампом —
            можно принудительно завершать строку.
            """
            if self.buffer:
                # Принудительно добавим \n и выведем
                buf = self.buffer
                self.buffer = ""
                self._write_line(buf + '\n')

            self.log_file.flush()
            self.real_stream.flush()

        def _write_line(self, full_line: str):
            """
            Здесь уже приходят "целые" строки (заканчиваются \n).
            Добавляем/не добавляем префикс, и печатаем в 2 потока: файл + реальный вывод.
            """
            # Если это stderr, проверяем, не начинается ли traceback
            if self.is_err and "Traceback (most recent call last):" in full_line:
                # Начали traceback, только эту строку префиксуем
                prefix = self._prefix()
                out_line = prefix + full_line
                self.in_traceback = True
            elif self.is_err and self.in_traceback:
                # Мы уже "внутри traceback", не префиксуем
                out_line = full_line
            else:
                # Обычный случай: префиксуем каждую строку
                prefix = self._prefix()
                out_line = prefix + full_line

            # Пишем и в файл, и в консоль
            self.log_file.write(out_line)
            self.log_file.flush()
            self.real_stream.write(out_line)
            self.real_stream.flush()

        def _prefix(self):
            """
            Формируем префикс вида "YYYY-MM-DD HH:MM:SS: "
            """
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ": "

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            base_dir = os.path.join(config.LOGS_ROOT, str(date.today()))
            os.makedirs(base_dir, exist_ok=True)

            out_file_path = os.path.join(base_dir, f'{command_name}.out')
            err_file_path = os.path.join(base_dir, f'{command_name}.err')

            # Открываем файлы
            f_out = open(out_file_path, 'a', encoding='utf-8')
            f_err = open(err_file_path, 'a', encoding='utf-8')

            # Сохраняем настоящие потоки
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            # Создаём наши Tee-объекты
            stdout_tee = Tee(old_stdout, f_out, is_err=False)
            stderr_tee = Tee(old_stderr, f_err, is_err=True)

            # Подменяем
            sys.stdout = stdout_tee
            sys.stderr = stderr_tee

            try:
                return func(*args, **kwargs)

            except Exception:
                # Если в команде произошло исключение,
                # выводим traceback в .err (где is_err=True), без префикса на внутренних строках
                traceback.print_exc(file=sys.stderr)
                # Завершаем программу, чтобы Click не печатал повторно
                sys.exit(1)

            finally:
                # Перед закрытием всё «прожмём» (flush), чтобы не осталось в буфере
                sys.stdout.flush()
                sys.stderr.flush()

                # Возвращаем потоки на место
                sys.stdout = old_stdout
                sys.stderr = old_stderr

                # Закрываем файлы (не забудьте!)
                f_out.close()
                f_err.close()

        return wrapper
    return decorator
