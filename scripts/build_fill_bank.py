"""Build the offline fill bank from an official NLTK WordNet 3.0 ZIP.

Development-only dependency: wordfreq==3.1.1. No corpus downloads occur at runtime.
Usage: python scripts/build_fill_bank.py /path/to/wordnet.zip
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile
from wordfreq import zipf_frequency


def build(source):
    output = Path(__file__).resolve().parents[1] / 'crossword_book' / 'data'
    entries = {}
    with zipfile.ZipFile(source) as archive:
        irregular = {}
        for line in archive.read('wordnet/noun.exc').decode().splitlines():
            plural,*bases = line.split()
            for base in bases:
                irregular.setdefault(base,[]).append(plural)
        for pos in ('noun', 'verb', 'adj', 'adv'):
            definitions = {}
            for line in archive.read(f'wordnet/data.{pos}').decode().splitlines():
                if line and line[0].isdigit():
                    record, gloss = line.split('|', 1)
                    clue = gloss.strip().split(';')[0].strip()
                    if len(clue) <= 110 and not re.search(r'\b(obscene|vulgar|offensive|derogatory)\b', gloss, re.I):
                        definitions[record.split()[0]] = clue[0].upper()+clue[1:]
            for line in archive.read(f'wordnet/index.{pos}').decode().splitlines():
                if not line or line[0].isspace():
                    continue
                fields = line.split()
                word = fields[0]
                if not word.isascii() or not word.isalpha() or not word.islower() or not 3 <= len(word) <= 13:
                    continue
                frequency = zipf_frequency(word, 'en')
                if frequency < 2.8:
                    continue
                offset = fields[6+int(fields[3])]
                clue = definitions.get(offset)
                if not clue or re.search(r'\b'+re.escape(word)+r'\b', clue, re.I):
                    continue
                tagged_senses = int(fields[5+int(fields[3])])
                previous = entries.get(word.upper())
                if previous is None or tagged_senses>previous[2]:
                    entries[word.upper()] = [clue, round(frequency, 2), tagged_senses]
                if pos=='noun' and tagged_senses and clue.lower().startswith(('a ', 'an ')):
                    if word in irregular:
                        plurals = irregular[word]
                    elif word.endswith(('s','x','z','ch','sh')):
                        plurals = [word+'es']
                    elif word.endswith('y') and word[-2] not in 'aeiou':
                        plurals = [word[:-1]+'ies']
                    else:
                        plurals = [word+'s']
                    for plural in plurals:
                        freq = zipf_frequency(plural,'en')
                        if 3<=len(plural)<=13 and plural.isascii() and plural.isalpha() and freq>=3.3:
                            definition = 'More than one '+re.sub(r'^an? ', '',clue,flags=re.I)
                            entries.setdefault(plural.upper(),[definition,round(freq,2),tagged_senses])
        (output/'WORDNET-LICENSE.txt').write_bytes(archive.read('wordnet/LICENSE'))
    # Avoid entries that are unsuitable for a general-interest animal book.
    excluded = {'SEX', 'SEXY', 'PENIS', 'VAGINA', 'FUCK', 'SHIT', 'CUNT', 'DICK', 'COCK', 'ASS', 'RAPE', 'NAZI', 'ANAL', 'ANUS', 'NUDE', 'ERECT', 'DILDO', 'SEMEN', 'SPERM', 'PORNO', 'PORN', 'SLUT', 'WHORE', 'BITCH', 'BASTARD', 'NEGRO', 'NIGGER', 'NIGGA', 'FAG', 'FAGGOT'}
    for word in excluded:
        entries.pop(word, None)
    overrides = output/'fill-overrides.txt'
    if overrides.exists():
        for line in overrides.read_text().splitlines():
            if line and not line.startswith('#'):
                word,clue = line.split('|')
                entries[word] = [clue, max(4.0,round(zipf_frequency(word.lower(),'en'),2)), 1]
    payload = {'source': 'Princeton WordNet 3.0 (NLTK distribution)',
               'source_url': 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip',
               'source_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
               'frequency_source': 'wordfreq 3.1.1; Zipf frequency used only to select and rank entries',
               'entries': dict(sorted(entries.items()))}
    (output/'fill.json').write_text(json.dumps(payload, indent=2)+'\n')
    print(f'Wrote {len(entries)} fill entries')


if __name__ == '__main__':
    build(sys.argv[1])
