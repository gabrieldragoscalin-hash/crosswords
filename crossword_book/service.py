"""Shared generation/export workflow used by the terminal and desktop app."""
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import shutil
import tempfile
from .core import make_book, load_entries, THEMES, EDITIONS
from .errors import check_cancel
from .frontmatter import DEFAULT_PUBLISHER, TITLES
from .pdf import write_pdf
from .series import SeriesSession


@dataclass(frozen=True)
class BookOptions:
    theme: str='dogs'
    difficulty: str='easy'
    count: int=50
    edition: str='standard'
    seed: int|None=None
    title: str|None=None
    subtitle: str|None=None
    publisher: str=DEFAULT_PUBLISHER
    copyright_year: int|None=None
    output: Path|None=None
    output_parent: Path=Path('dist')
    avoid_repeats: bool=True
    series: str|None=None
    history: Path=Path('.crossword-series/history.sqlite3')


def generate_book(options,progress=None,cancel=None):
    if options.theme not in THEMES: raise ValueError('Choose a supported theme')
    if options.edition not in EDITIONS: raise ValueError('Unknown edition')
    if not isinstance(options.count,int) or options.count<1: raise ValueError('Count must be a positive integer')
    if not options.publisher.strip(): raise ValueError('Publisher cannot be empty')
    mode={'medium':'normal','progressive':'incremental'}.get(options.difficulty,options.difficulty)
    if mode not in ('easy','normal','hard','incremental'): raise ValueError('Unknown difficulty')
    year=options.copyright_year if options.copyright_year is not None else datetime.now(timezone.utc).year
    if not 1000<=year<=9999: raise ValueError('Copyright year must have four digits')
    if options.series and not options.avoid_repeats:
        raise ValueError('Series generation requires repeat avoidance')
    seed=options.seed if options.seed is not None else secrets.randbits(32)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    output=Path(options.output) if options.output is not None else Path(options.output_parent)/f'{options.theme}-{mode}-{options.edition}-{stamp}'
    if output.exists(): raise ValueError('Output directory already exists; choose a new directory')
    check_cancel(cancel)
    session=SeriesSession(options.history,options.series,options.theme) if options.series else nullcontext(None)
    with session as history:
        book=make_book(options.count,mode,options.theme,seed,progress=progress,edition=options.edition,
                       avoid_repeats=options.avoid_repeats,prior_usage=history.usage if history else None,
                       excluded_grids=history.grids if history else None,
                       excluded_titles=history.titles if history else None,cancel=cancel)
        title=options.title or TITLES[options.theme]
        book.update(title=title,publisher=options.publisher.strip(),copyright_year=year,subtitle=options.subtitle)
        if history:
            book.update(series=options.series,volume=history.volume)
        output.parent.mkdir(parents=True,exist_ok=True)
        published=False
        try:
            with tempfile.TemporaryDirectory(prefix='.crossword-',dir=output.parent) as temporary:
                folder=Path(temporary)
                write_pdf(book,folder/'book.pdf',title,cancel=cancel)
                (folder/'book.json').write_text(json.dumps(book,indent=2)+'\n',encoding='utf-8')
                wordlists=folder/'wordlists';wordlists.mkdir()
                for level in ('easy','hard'):
                    (wordlists/f'{options.theme}-{level}.txt').write_text(''.join(
                        f'{e.answer}|{getattr(e,level)}\n' for e in load_entries(options.theme)),encoding='utf-8')
                used={(e['answer'],e['clue']) for p in book['puzzles'] for e in p['entries']}
                (wordlists/'used-answers.txt').write_text(''.join(f'{word}|{clue}\n' for word,clue in sorted(used)),encoding='utf-8')
                notices=folder/'licenses';notices.mkdir()
                for name in ('WORDNET-LICENSE.txt','WORDFREQ-NOTICE.txt','WORDFREQ-CODE-LICENSE.txt','CC-BY-SA-4.0.txt'):
                    shutil.copyfile(Path(__file__).parent/'data'/name,notices/name)
                check_cancel(cancel)
                if history: history.record(book,output)
                if output.exists(): raise ValueError('Output directory was created by another process')
                folder.rename(output)
                published=True
                if history: history.commit()
        except BaseException:
            if published: shutil.rmtree(output)
            raise
    return output
