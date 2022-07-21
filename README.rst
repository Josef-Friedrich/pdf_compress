.. image:: http://img.shields.io/pypi/v/pdf-compress.svg
    :target: https://pypi.org/project/pdf-compress
    :alt: This package on the Python Package Index

.. image:: https://github.com/Josef-Friedrich/pdf_compress/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/Josef-Friedrich/pdf_compress/actions/workflows/tests.yml
    :alt: Tests

pdf_compress
============

Convert and compress PDF scans. Make scans suitable for imslp.org
(International Music Score Library Project). See also
https://imslp.org/wiki/IMSLP:Scanning_music_scores. The output files are
monochrome bitmap images at a resolution of 600 dpi and the compression
format CCITT group 4.

:: 

    usage: pdf-compress.py [-h] [-c] [-m] [-N] [-v] [-V]
                           {convert,con,c,extract,ex,e,join,jn,j,samples,sp,s,unify,un,u}
                           ...

    Convert and compress PDF scans. Make scans suitable for imslp.org
    (International Music Score Library Project). See also
    https://imslp.org/wiki/IMSLP:Scanning_music_scores The output files are
    monochrome bitmap images at a resolution of 600 dpi and the compression format
    CCITT group 4.

    positional arguments:
      {convert,con,c,extract,ex,e,join,jn,j,samples,sp,s,unify,un,u}
                            Subcommand

    options:
      -h, --help            show this help message and exit
      -c, --colorize        Colorize the terminal output.
      -m, --multiprocessing
                            Use multiprocessing to run commands in parallel.
      -N, --no-cleanup      Don’t clean up the temporary files.
      -v, --verbose         Make the command line output more verbose.
      -V, --version         show program's version number and exit

