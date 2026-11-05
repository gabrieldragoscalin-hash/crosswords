"""Fully checked blocked crosswords, filled with a bounded constraint solver."""
from collections import deque, Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
import json
import hashlib
from pathlib import Path
import random

from .themes import THEMES
LEVELS = {'easy': (9, 3.5), 'normal': (11, 3.2), 'hard': (13, 2.8)}
DATA = Path(__file__).parent / 'data'
EDITIONS = ('standard', 'large-print')


def grid_signature(grid):
    return hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()



@dataclass(frozen=True)
class Entry:
    answer: str
    easy: str
    hard: str


@lru_cache(maxsize=len(THEMES))
def load_entries(theme):
    if theme not in THEMES:
        raise ValueError('Unknown theme')
    entries = []
    for line in (DATA / f'{theme}.txt').read_text().splitlines():
        if line and not line.startswith('#'):
            word, easy, hard = line.split('|')
            if not word.isascii() or not word.isalpha() or word != word.upper():
                raise ValueError(f'Invalid answer: {word}')
            entries.append(Entry(word, easy, hard))
    if len({e.answer for e in entries}) != len(entries):
        raise ValueError(f'Duplicate answers in {theme}')
    return tuple(entries)


def slots_for(pattern):
    """Return every maximal white run, including illegal short runs for validation."""
    n = len(pattern)
    slots = []
    for r in range(n):
        for c in range(n):
            if pattern[r][c] == '#':
                continue
            for direction, dr, dc in [('across', 0, 1), ('down', 1, 0)]:
                if r-dr >= 0 and c-dc >= 0 and pattern[r-dr][c-dc] != '#':
                    continue
                cells, rr, cc = [], r, c
                while rr < n and cc < n and pattern[rr][cc] != '#':
                    cells.append((rr, cc))
                    rr, cc = rr+dr, cc+dc
                slots.append((direction, tuple(cells)))
    return slots


def is_connected(pattern):
    white = {(r,c) for r,row in enumerate(pattern) for c,char in enumerate(row) if char != '#'}
    if not white:
        return False
    seen, todo = set(), [min(white)]
    while todo:
        r,c = todo.pop()
        if (r,c) in seen:
            continue
        seen.add((r,c))
        todo.extend(p for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if p in white and p not in seen)
    return white == seen


def make_pattern(size, rng):
    """Rotational symmetry, connected whites, no runs shorter than three."""
    grid = [['.' for _ in range(size)] for _ in range(size)]
    pairs = [(r,c) for r in range(size) for c in range(size) if (r,c) <= (size-1-r,size-1-c)]
    rng.shuffle(pairs)
    for r,c in pairs:
        other = size-1-r, size-1-c
        grid[r][c] = grid[other[0]][other[1]] = '#'
        if any(len(cells)<3 for _,cells in slots_for(grid)) or not is_connected(grid):
            grid[r][c] = grid[other[0]][other[1]] = '.'
        if sum(row.count('#') for row in grid) >= size*size*.25:
            break
    return tuple(''.join(row) for row in grid)


class Vocabulary:
    def __init__(self, theme, level, edition='standard'):
        from .clues import fill_records
        self.themed = {e.answer:e for e in load_entries(theme)}
        records = fill_records()
        floor = LEVELS[level][1]
        self.clues = {w:record[0] for w,record in records.items()
                      if record[1] >= floor and (level!='easy' or record[2]>0)
                      and (edition!='large-print' or len(record[0])<=52)}
        self.frequency = {w:record[1] for w,record in records.items() if w in self.clues}
        self.clues.update({w:e.easy for w,e in self.themed.items()})
        self.frequency.update({w:5.0 for w in self.themed})
        self.words, self.indices, self.masks, self.theme_masks = {}, {}, {}, {}
        for length in range(3,14):
            words = sorted((w for w in self.clues if len(w)==length), key=lambda w:(-self.frequency[w],w))
            self.words[length] = words
            self.indices[length] = {word:i for i,word in enumerate(words)}
            masks = [{chr(65+i):0 for i in range(26)} for _ in range(length)]
            theme_mask = 0
            for i,word in enumerate(words):
                bit = 1 << i
                for p,char in enumerate(word):
                    masks[p][char] |= bit
                if word in self.themed:
                    theme_mask |= bit
            self.masks[length] = masks
            self.theme_masks[length] = theme_mask


@lru_cache(maxsize=len(THEMES)*len(LEVELS)*len(EDITIONS))
def vocabulary(theme, level, edition='standard'):
    return Vocabulary(theme, level, edition)


def fill_pattern(pattern, vocab, rng, node_limit=200, word_usage=None, cancel=None, fresh_theme_preference=True):
    from .errors import check_cancel
    usage=word_usage or {}
    slots = slots_for(pattern)
    lengths = [len(cells) for _,cells in slots]
    if any(n<3 or not vocab.words.get(n) for n in lengths):
        return None
    locations = {}
    neighbors = [[] for _ in slots]
    for i,(_,cells) in enumerate(slots):
        for pos,cell in enumerate(cells):
            if cell in locations:
                j,otherpos = locations[cell]
                neighbors[i].append((j,pos,otherpos))
                neighbors[j].append((i,otherpos,pos))
            else:
                locations[cell] = i,pos
    # At least two distinct, substantial theme answers, preferably parallel.
    options = [i for i,n in enumerate(lengths) if n>=5 and vocab.theme_masks[n]]
    pairs = [(i,j) for i,j in combinations(options,2) if slots[i][0]==slots[j][0]]
    if not pairs:
        return None
    domains = [(1 << len(vocab.words[n]))-1 for n in lengths]
    weights = [vocab.theme_masks[lengths[i]].bit_count()*vocab.theme_masks[lengths[j]].bit_count()
               for i,j in pairs]
    anchor_a,anchor_b = rng.choices(pairs,weights=weights,k=1)[0]
    for i in (anchor_a,anchor_b):
        allowed=vocab.theme_masks[lengths[i]]
        if usage and fresh_theme_preference and rng.random()<.8:
            words=vocab.words[lengths[i]]
            indices=[k for k,w in enumerate(words) if allowed & (1<<k)]
            least=min(usage.get(words[k],0) for k in indices)
            allowed=sum(1<<k for k in indices if usage.get(words[k],0)==least)
        domains[i] &= allowed

    def propagate(ds, queue):
        while queue:
            i = queue.popleft()
            domain = ds[i]
            if not domain:
                return False
            if domain.bit_count() == 1:
                # No answer is repeated within a puzzle.
                for j in range(len(slots)):
                    if j != i and lengths[j] == lengths[i] and ds[j] & domain:
                        ds[j] &= ~domain
                        if not ds[j]:
                            return False
                        queue.append(j)
            for j,pos,otherpos in neighbors[i]:
                source = vocab.masks[lengths[i]][pos]
                target = vocab.masks[lengths[j]][otherpos]
                support = 0
                for char,mask in source.items():
                    if domain & mask:
                        support |= target[char]
                new = ds[j] & support
                if new != ds[j]:
                    if not new:
                        return False
                    ds[j] = new
                    queue.append(j)
        return True

    if not propagate(domains, deque(range(len(slots)))):
        return None
    nodes = 0

    def search(ds):
        nonlocal nodes
        check_cancel(cancel)
        nodes += 1
        if nodes > node_limit:
            return None
        unresolved = [i for i,d in enumerate(ds) if d.bit_count()>1]
        if not unresolved:
            return ds
        i = min(unresolved, key=lambda i:(ds[i].bit_count(),-len(neighbors[i])))
        bits, domain = [], ds[i]
        while domain:
            bit = domain & -domain
            bits.append(bit)
            domain ^= bit
        # Prefer familiar fill while allowing reproducible variation.
        scored = [(bit, rng.random()+1/(1+k*.06)
                   -4*usage.get(vocab.words[lengths[i]][bit.bit_length()-1],0))
                  for k,bit in enumerate(bits)]
        scored.sort(key=lambda item:-item[1])
        for bit,_ in scored:
            child = ds[:]
            child[i] = bit
            if propagate(child,deque([i])):
                result = search(child)
                if result:
                    return result
            if nodes > node_limit:
                break
        return None

    result = search(domains)
    if result is None:
        return None
    return [(direction,cells,vocab.words[len(cells)][domain.bit_length()-1])
            for (direction,cells),domain in zip(slots,result)]


def generate(theme, difficulty, rng, edition='standard', word_usage=None, cancel=None):
    from .errors import check_cancel
    if theme not in THEMES or difficulty not in LEVELS or edition not in EDITIONS:
        raise ValueError('Unknown theme or difficulty')
    vocab = vocabulary(theme,difficulty,edition)
    size = 8 if edition=='large-print' else LEVELS[difficulty][0]
    # A long series must still be fillable after common crossing words are used.
    # Relax the preference after unsuccessful patterns; exact grids stay excluded.
    relaxed_usage={w:.15*n/(1+n) for w,n in (word_usage or {}).items()}
    for attempt in range(1000):
        check_cancel(cancel)
        pattern = make_pattern(size,rng)
        # Avoid long unfillable slots and overly blocked grids.
        if any(len(cells)>10 for _,cells in slots_for(pattern)):
            continue
        if edition=='large-print' and len(slots_for(pattern))>28:
            continue
        fill = fill_pattern(pattern,vocab,rng,
                            word_usage=word_usage if attempt<100 else relaxed_usage,
                            cancel=cancel,fresh_theme_preference=attempt<100)
        if fill is None:
            continue
        grid = [['' for _ in range(size)] for _ in range(size)]
        starts = sorted({cells[0] for _,cells,_ in fill})
        numbers = {point:i+1 for i,point in enumerate(starts)}
        entries = []
        for direction,cells,word in fill:
            for (r,c),char in zip(cells,word):
                grid[r][c] = char
            themed = word in vocab.themed
            if themed:
                source = vocab.themed[word]
                clue = source.hard if difficulty=='hard' or (difficulty=='normal' and rng.random()<.5) else source.easy
            else:
                clue = vocab.clues[word]
            entries.append(dict(answer=word,clue=clue,row=cells[0][0],col=cells[0][1],
                                direction=direction,number=numbers[cells[0]],themed=themed))
        return dict(theme=theme,difficulty=difficulty,edition=edition,grid=grid,
                    checked_fraction=1.0,theme_answer_count=sum(e['themed'] for e in entries),
                    entries=sorted(entries,key=lambda e:(e['number'],e['direction'])))
    raise RuntimeError(f'Cannot fill a dense {difficulty} {theme} grid after 1000 attempts; try another seed or expand the word banks')


def make_book(count=50, mode='incremental', theme='dogs', seed=1, progress=None,
              edition='standard', avoid_repeats=True, prior_usage=None,
              excluded_grids=None, excluded_titles=None, cancel=None):
    from .pdf import plan_puzzle, PageFitError
    if not isinstance(count,int) or count<1:
        raise ValueError('Puzzle count must be a positive integer')
    if mode=='progressive':
        mode='incremental'
    if mode not in (*LEVELS,'incremental'):
        raise ValueError('Unknown difficulty mode')
    if theme not in THEMES:
        raise ValueError('Unknown theme')
    if edition not in EDITIONS:
        raise ValueError('Unknown edition')
    usage=Counter(prior_usage or {})
    rng, puzzles, seen = random.Random(seed), [], set(excluded_grids or ())
    for i in range(count):
        level = tuple(LEVELS)[min(2,i*3//count)] if mode=='incremental' else mode
        for _ in range(30):
            puzzle = generate(theme,level,rng,edition=edition,
                              word_usage=usage if avoid_repeats else None,cancel=cancel)
            try:
                plan_puzzle(puzzle)
            except PageFitError:
                # Select another complete fill instead of adding a clue page or
                # shrinking type below the print layout's minimum size.
                continue
            signature = grid_signature(puzzle['grid'])
            if signature not in seen:
                seen.add(signature)
                puzzle['number']=i+1
                puzzles.append(puzzle)
                usage.update(e['answer'] for e in puzzle['entries'])
                if progress:
                    progress(i+1,count)
                break
        else:
            raise RuntimeError('Could not generate a unique puzzle that fits one page; try another seed or shorter clues')
    from .puzzle_titles import assign_puzzle_titles
    book=dict(seed=seed,mode=mode,theme=theme,themes=[theme],edition=edition,
              avoid_repeats=avoid_repeats,grid_style='fully_checked',puzzles=puzzles)
    assign_puzzle_titles(book,excluded_titles=excluded_titles)
    return book
