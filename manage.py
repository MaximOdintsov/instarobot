#!.venv/bin/python

import click
import os
import importlib

import asyncio
from robot.database.orm import create_tables, async_engine
from robot import config


def load_commands(cli):
    """
    Автоматически загружает все команды из папки config.COMMANDS_ROOT.
    """
    for filename in os.listdir(config.COMMANDS_ROOT):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            module_path = f'robot.commands.{module_name}'
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
