# Single-theme crossword book generator

Create **dense, newspaper-style crosswords**: every white square belongs to
both an Across answer and a Down answer. Grids are connected, have rotationally
symmetric black squares, and contain no one- or two-letter answers.

Each book has **one theme**, with at least two substantial theme answers per
puzzle and general English crossing fill. Choose dogs, cats, wildlife, animals,
birds, or fish. The interior is **8.5 × 11 inches**, with numbered clues and
solutions. No API key, online AI service, or runtime download is required.

Theme-answer squares have a light **20% black gray fill**, suitable for a
black-and-white interior, and their clues are marked with an asterisk (`*`).
The same shading appears in the solutions. Generic answers remain unshaded
except where they intersect a theme answer. A legend explains the markings on
each puzzle page. No color conversion is needed; check a printed proof to assess
the gray tone on your chosen paper.

## Install and run

Use Python 3.10 or later. From this checkout:

```sh
python -m pip install -e .
python crosswordgenerator.py dogs easy
python crosswordgenerator.py dogs easy 50
python crosswordgenerator.py cats normal 50
python crosswordgenerator.py wildlife hard 75
python crosswordgenerator.py birds incremental 50
python crosswordgenerator.py fish easy 100
python crosswordgenerator.py animals hard 50
```

On Windows, `py` can replace `python`. On Linux/macOS, use `python3` if needed.
The installed command `crossword-book dogs easy 50` works the same way.

The count defaults to **50**; any positive count is accepted, including 1 for a
quick preview. Each run creates a new directory under `dist/` and prints the
PDF path. Generation progress appears after each completed puzzle. Large books
can take several minutes because every grid must be solved consistently.

Optional settings:

```sh
python crosswordgenerator.py dogs incremental 50 --seed 42 --title "Dog Crossword Adventures" --output dist/my-dog-book
```

`--seed` makes the book reproducible with this version of the generator and word
banks. Without it, each run receives a random seed, saved in `book.json`.
`--output` must name a new directory; existing files are never overwritten.
Title pages use a double border, theme motifs, a crossword illustration, the
actual puzzle count and difficulty, and Quickberry Books branding. They do not
claim to be a large-print edition. Customize the publication details with
`--title`, `--subtitle`, `--publisher`, and `--copyright-year` (defaults to the
current year). These settings are retained in `book.json`.
`wildlife`, `wild-life`, and quoted `"wild life"` refer to the same theme.
`progressive` is accepted as an alias for `incremental`.
`medium` is accepted as an alias for `normal`.

## Difficulty

| Mode | Grid | Vocabulary and clues |
| --- | --- | --- |
| Easy | 9 × 9 | More familiar fill; straightforward theme clues |
| Normal | 11 × 11 | Broader fill; mixed theme clue styles |
| Hard | 13 × 13 | Broader vocabulary; technical theme clues |
| Incremental | 9 → 11 → 13 | Ordered easy, normal, hard stages |

For 50 incremental puzzles, the stages contain 17 easy, 17 normal, and 16 hard
puzzles. Difficulty is a construction heuristic, not a human-tested rating.
There is no change of theme within an incremental book.

## Output

- `book.pdf`: title page, copyright, How to Play, puzzles, solutions, dictionary
  credits, and a final thank-you page.
- `book.json`: seed, theme, mode, exact grids, numbered answers, clues, and theme flags.
- `wordlists/<theme>-easy.txt` and `<theme>-hard.txt`: theme entries in `WORD|clue` format.
- `wordlists/used-answers.txt`: all distinct answer/clue pairs used in that book,
  including general fill.
- `licenses/`: source attribution and license texts accompanying the dictionary.

Each crossword and **all of its clues occupy exactly one page**. Clues flow
beside and underneath the grid in three columns. The layout balances grid size
and type size (at least 8.5 points), retaining every clue. A fill that cannot fit
is regenerated instead of adding another page. Solutions are arranged four per
page. A 50-puzzle book has **68 pages**: three opening pages, 50 puzzle pages, 13
solution pages, one credits page, and a final thank-you page. How to Play
explains the shading and clue marks and automatically points to the first
solution page (page 54 for 50 puzzles). Interior page numbers match the PDF's
physical pages; title and copyright pages have no printed number.
Pages use US Letter dimensions,
black-and-white interiors, and side margins of at least 0.58 inches. A cover
is not included.

There are 24–46 starter theme entries per theme and over 21,000 general fill entries.
Grids cannot repeat within a book, but answers and clues can. Books with different
seeds can also share answers. Expand the theme banks and review clues and a printed
proof before publishing commercial editions. Dictionary definitions are not all
polished crossword clues; some fill uses abbreviations or proper names.

## Content and implementation

Edit `crossword_book/data/<theme>.txt` using:

```text
ANSWER|straightforward clue|harder clue
```

Answers must be uppercase ASCII letters without spaces, and unique within that
file. `fill-overrides.txt` supplies editorial general-fill clues as `ANSWER|clue`.
The bundled `fill.json` contains dictionary definitions and familiarity ratings.
Changes to the overrides require rebuilding the fill bank.

The engine constructs a blocked pattern, finds all Across/Down slots, and fills
both directions together using constraint propagation and backtracking. At least
two slots of five or more letters are restricted to the selected theme bank.
It rejects failed fills; it never falls back to the earlier sparse grid style.
Search is bounded, so an unusual seed or restrictive bank can fail with a clear
error. Outputs are published only after the entire book has generated successfully.

### Dictionary sources

Definitions are adapted from **Princeton WordNet 3.0**, under the included
`WORDNET-LICENSE.txt`. Familiarity scores use **wordfreq 3.1.1** by Robyn Speer;
its code is Apache-2.0 and its data is CC BY-SA 4.0. The adapted frequency data in
`fill.json` is distributed under CC BY-SA 4.0. See `WORDFREQ-NOTICE.txt`,
`WORDFREQ-CODE-LICENSE.txt`, and `CC-BY-SA-4.0.txt` in `crossword_book/data/` for
full attribution and terms. WordNet source SHA-256 and source URL are stored in
the JSON. Source notices also accompany each generated book.

To rebuild the bundled bank (development only), install `wordfreq==3.1.1` and run:

```sh
python scripts/build_fill_bank.py /path/to/wordnet.zip
```

Use the official NLTK WordNet distribution linked in `fill.json`. Rebuilding
performs vocabulary selection, clue shortening, plural generation, and editorial
overrides. It is not required to generate books from the checked-in bank.

## Validation

```sh
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
```

Tests check all six themes at all three levels, matching crossing letters,
100% double coverage, clue numbering, minimum answer length, unique answers,
connected white squares, block symmetry, theme presence, single-theme incremental
books, reproducibility, CLI output protection, one page per puzzle, and the
presence of every clue on that same page.

Use the existing isolated checkout for development; a separate worktree is unnecessary.
Generated books under `dist/` are ignored by Git.
