#!/usr/bin/env python3
from hijacked_log import Logger
import argparse as argp

import sys
import os

__doc__ = 'Documentation should be here...'

parsers = ['raw_lines', 'whatsapp_export', 'telegram_export', 'paragraphs']

class Parser: ...
class LinesParser(Parser): ...
class ParagraphsParser(Parser): ...
class WhatsappParser(Parser): ...
class TelegramParser(Parser): ...

def parse_args() -> argp.Namespace:
    parser = argp.ArgumentParser(description=__doc__, formatter_class=argp.RawDescriptionHelpFormatter)

    parser.add_argument('infile',  '-i', '--infile',  required=True,  help="Input file",    default=sys.stdin,                   type=argp.FileType('r', encoding='utf-8'))
    parser.add_argument('outfile', '-o', '--outfile', required=True,  help="Output file",   default=sys.stdout,                  type=argp.FileType('w', encoding='utf-8'))
    parser.add_argument(           '-p', '--parser',  required=False, help="Parser to use", default='raw_lines', choices=parsers)

    args = parser.parse_args()

    return args

def main(logger: Logger):
    args: argp.Namespace = parse_args()

    logger.log('')

    print(args)

if __name__ == '__main__':
    res = 0

    try:
        main(Logger(os.path.join('LOGs')))
    except Exception as e:
        res = 1
        print(e)

    sys.exit(res)
