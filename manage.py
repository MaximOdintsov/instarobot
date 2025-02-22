#!.venv/bin/python

import click
import importlib
import asyncio
from pathlib import Path

from robot.database.orm import create_tables, async_engine
from robot.conf import settings


def load_commands(cli):
    """
    Автоматически загружает все команды из папки config.COMMANDS_ROOT.
    """
    root_path = Path(settings.COMMANDS_ROOT)
    path_list = root_path.rglob('*.py')
    for path in path_list:
        if path.name == '__init__.py':
            continue
        module_name = path.stem
        parent = path.parent.as_posix().replace("/", ".")
        module_path = f'{parent}.{module_name}'

        try:
            module = importlib.import_module(module_path)
            # Ищем объекты, являющиеся командами (или группами) Click
            for attr_name in dir(module):
                obj = getattr(module, attr_name)
                if isinstance(obj, click.Command):
                    cli.add_command(obj)
        except Exception as e:
            click.echo(f"Не удалось загрузить команду из {module_name}: {e}", err=True)


@click.group()
def cli():
    """Менеджер команд"""
    pass


def main():
    load_commands(cli)
    cli()


if __name__ == '__main__':
    asyncio.run(create_tables(async_engine))
    main()
