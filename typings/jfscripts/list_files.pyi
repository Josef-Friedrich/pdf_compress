"""
This type stub file was generated by pyright.
"""

def is_glob(string): # -> bool:
    ...

def common_path(paths): # -> LiteralString | str:
    ...

def list_files(files, default_glob=...): # -> list[Unknown]:
    """
    :param list files: A list of file paths or a single element list containing
      a glob string.

    :param string default_glob: A default glob pattern like “(asterisk).txt”.
      This argument is only taken into account, if “element” is a list with
      only one entry and this entry is a path to a directory.
    """
    ...

def doc_examples(command_name=..., extension=..., indent_spaces=..., inline=...): # -> str:
    ...

def get_parser(): # -> ArgumentParser:
    """The argument parser for the command line interface.

    :return: A ArgumentParser object.
    :rtype: argparse.ArgumentParser
    """
    ...

def main(): # -> None:
    ...

if __name__ == '__main__':
    ...