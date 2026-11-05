"""Single-theme book command line interface."""
import argparse
from pathlib import Path
import re
import sqlite3
from .themes import THEMES, ALIASES
from .errors import GenerationCancelled
from .service import BookOptions,generate_book


def normalize_theme(value):
    normalized=re.sub(r'[\s_-]+','',value.lower())
    normalized=ALIASES.get(normalized,normalized)
    if normalized not in THEMES:
        raise argparse.ArgumentTypeError('Choose one of: '+', '.join(THEMES))
    return normalized


def main(argv=None):
    parser=argparse.ArgumentParser(description='Create a single-theme, fully checked crossword book (8.5 x 11 inches).')
    parser.add_argument('theme',type=normalize_theme,help=', '.join(THEMES))
    parser.add_argument('difficulty',choices=['easy','normal','medium','hard','incremental','progressive'])
    parser.add_argument('count',type=int,nargs='?',default=50,help='number of puzzles (default: 50)')
    parser.add_argument('--seed',type=int)
    parser.add_argument('--title')
    parser.add_argument('--subtitle')
    parser.add_argument('--publisher',default='Quirckberry Books')
    parser.add_argument('--copyright-year',type=int)
    parser.add_argument('--edition',choices=['standard','large-print'],default='standard')
    parser.add_argument('--allow-repeats',action='store_true',help='disable preference for unused answers')
    parser.add_argument('--series',help='series name; advances the volume and remembers past content')
    parser.add_argument('--history',type=Path,default=Path('.crossword-series/history.sqlite3'))
    parser.add_argument('--output',type=Path,help='new output directory')
    args=parser.parse_args(argv)
    if args.count<1: parser.error('count must be a positive integer')
    try:
        options=BookOptions(theme=args.theme,difficulty=args.difficulty,count=args.count,seed=args.seed,
                            title=args.title,subtitle=args.subtitle,publisher=args.publisher,
                            copyright_year=args.copyright_year,edition=args.edition,
                            avoid_repeats=not args.allow_repeats,series=args.series,history=args.history,output=args.output)
        print(f'Generating {args.count} {args.theme} crosswords ({args.difficulty}, {args.edition})',flush=True)
        output=generate_book(options,progress=lambda done,total:print(f'  Puzzle {done}/{total}',flush=True))
    except (RuntimeError,ValueError,OSError,sqlite3.Error,GenerationCancelled) as error:
        parser.exit(1,f'Generation failed: {error}\n')
    print(f'Created {output/"book.pdf"}',flush=True)


if __name__=='__main__':
    main()
