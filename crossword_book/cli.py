"""Single-theme book command line interface."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import tempfile
from .core import THEMES, make_book, load_entries
from .pdf import write_pdf
from .frontmatter import DEFAULT_PUBLISHER, TITLES


def normalize_theme(value):
    normalized = re.sub(r'[\s_-]+', '', value.lower())
    if normalized not in THEMES:
        raise argparse.ArgumentTypeError('Choose one of: '+', '.join(THEMES))
    return normalized


def main(argv=None):
    parser = argparse.ArgumentParser(description='Create a single-theme, fully checked crossword book (8.5 x 11 inches).')
    parser.add_argument('theme', type=normalize_theme, help='dogs, cats, wildlife, animals, birds, or fish')
    parser.add_argument('difficulty', choices=['easy','normal','medium','hard','incremental','progressive'])
    parser.add_argument('count', type=int, nargs='?', default=50, help='number of puzzles (default: 50)')
    parser.add_argument('--seed', type=int, default=None, help='set a seed to reproduce a book')
    parser.add_argument('--title', default=None)
    parser.add_argument('--subtitle', default=None)
    parser.add_argument('--publisher', default=DEFAULT_PUBLISHER)
    parser.add_argument('--copyright-year', type=int, default=datetime.now(timezone.utc).year)
    parser.add_argument('--output', type=Path, default=None, help='new output directory')
    args = parser.parse_args(argv)
    if args.count<1:
        parser.error('count must be a positive integer')
    if not args.publisher.strip():
        parser.error('publisher cannot be empty')
    if not 1000 <= args.copyright_year <= 9999:
        parser.error('copyright year must have four digits')
    if args.difficulty=='progressive':
        args.difficulty='incremental'
    if args.difficulty=='medium':
        args.difficulty='normal'
    if args.seed is None:
        import secrets
        args.seed = secrets.randbits(32)
    if args.output is None:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
        args.output = Path('dist')/f'{args.theme}-{args.difficulty}-{args.count}-{stamp}'
    if args.output.exists():
        parser.error('Output directory already exists; choose a new --output directory')
    title = args.title or TITLES[args.theme]
    print(f'Generating {args.count} {args.theme} crosswords ({args.difficulty}); seed {args.seed}', flush=True)
    try:
        book = make_book(args.count,args.difficulty,args.theme,args.seed,
                         progress=lambda done,total: print(f'  Puzzle {done}/{total}',flush=True))
        book.update(publisher=args.publisher, copyright_year=args.copyright_year,
                    subtitle=args.subtitle)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        # No partial book is published if PDF layout or generation fails.
        with tempfile.TemporaryDirectory(prefix='.crossword-',dir=args.output.parent) as temporary:
            output = Path(temporary)
            write_pdf(book,output/'book.pdf',title)
            book['title'] = title
            (output/'book.json').write_text(json.dumps(book,indent=2)+'\n',encoding='utf-8')
            wordlists = output/'wordlists'
            wordlists.mkdir()
            for level in ('easy','hard'):
                (wordlists/f'{args.theme}-{level}.txt').write_text(''.join(
                    f'{e.answer}|{getattr(e,level)}\n' for e in load_entries(args.theme)),encoding='utf-8')
            used = {(e['answer'],e['clue']) for p in book['puzzles'] for e in p['entries']}
            (wordlists/'used-answers.txt').write_text(''.join(f'{word}|{clue}\n' for word,clue in sorted(used)),encoding='utf-8')
            notices = output/'licenses'
            notices.mkdir()
            for name in ('WORDNET-LICENSE.txt','WORDFREQ-NOTICE.txt','WORDFREQ-CODE-LICENSE.txt','CC-BY-SA-4.0.txt'):
                shutil.copyfile(Path(__file__).parent/'data'/name,notices/name)
            # Rename only after every output is complete; destination must be new.
            Path(temporary).rename(args.output)
    except (RuntimeError,ValueError) as error:
        parser.exit(1,f'Generation failed: {error}\n')
    print(f'Created {args.output / "book.pdf"}',flush=True)


if __name__=='__main__':
    main()
