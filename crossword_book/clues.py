"""Concise fill clues with live editorial overrides; no clipped definitions."""
from functools import lru_cache
import json
from pathlib import Path
import re

DATA=Path(__file__).parent/'data'
_UNSUITABLE=re.compile(r'\b(genus|subgenus|monotypic|surgical|prostate|genital|sexual|sexually|penis|vagina|phallus|obscene|vulgar|derogatory|racial slur)\b',re.I)


def natural_clue(text, answer=None, limit=72):
    text=' '.join(text.split()).strip().rstrip('.')
    if not text or _UNSUITABLE.search(text) or text.startswith('More than one '):
        return None
    # Preserve whole meanings: rewrite stock dictionary phrasing, never slice it.
    for old,new in [('A person who ','One who '),('Someone who ','One who '),
                    ('Any of various ','Type of '),('Any of several ','Type of '),
                    ('The act of ','Act of '),('A kind of ','Type of ')]:
        if text.startswith(old): text=new+text[len(old):];break
    text=re.sub(r'^(?:A|An|The) ', '',text)
    text=text[0].upper()+text[1:]
    if len(text)>limit or (answer and re.search(r'\b'+re.escape(answer)+r'\b',text,re.I)):
        return None
    return text


@lru_cache(maxsize=1)
def fill_records():
    records={}
    for answer,(definition,frequency,tagged) in json.loads((DATA/'fill.json').read_text())['entries'].items():
        clue=natural_clue(definition,answer)
        if clue: records[answer]=(clue,frequency,tagged)
    for line in (DATA/'fill-overrides.txt').read_text().splitlines():
        if not line or line.startswith('#'):continue
        answer,clue=line.split('|')
        if not answer.isascii() or not answer.isalpha() or answer!=answer.upper():
            raise ValueError(f'Invalid editorial answer: {answer}')
        if not clue.strip() or len(clue)>72:
            raise ValueError(f'Editorial clue must be 1–72 characters: {answer}')
        previous=records.get(answer,('',4.,1))
        records[answer]=(clue.strip(),max(4.,previous[1]),max(1,previous[2]))
    return records
