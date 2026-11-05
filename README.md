# Quickberry Books crossword generator

Generate English, single-theme crossword book interiors at **8.5 × 11 inches**.
Choose **dogs, cats, wildlife, animals, birds, fish, gardening, baking, travel,
space, or Christmas**, and easy, medium/normal, hard, or incremental difficulty.
Every white square belongs to both an Across and a Down answer. Grids are connected, with symmetric blocks and no answers
shorter than three letters.

## Install

Requires Python 3.10 or newer. From the checkout:

```sh
python -m pip install -e .
```

On Windows, `py` can replace `python`; on Linux/macOS, use `python3` if needed.

## Desktop app

Double-click **crosswordgui.pyw** on Windows after installing dependencies, or run:

```sh
python crosswordgui.py
```

The installed launcher is `crossword-book-gui`. Choose your theme, difficulty,
count, edition, publishing details, and output folder, then click **Generate
book**. A progress bar tracks the work. Generation runs in the background, with
**Cancel**, **Open PDF**, and **Open folder** controls. Cancellation does not save
an incomplete book or advance a series volume.

Tkinter is included in standard Windows and macOS Python installers. On Linux,
install your distribution's `python3-tk` package if needed. A graphical desktop
is required; the command-line generator also works on headless machines.

## Command line

Existing commands continue to work:

```sh
python crosswordgenerator.py dogs easy 50
python crosswordgenerator.py cats medium 50
python crosswordgenerator.py wildlife hard 75
python crosswordgenerator.py birds incremental 50
python crosswordgenerator.py fish easy 100
python crosswordgenerator.py animals hard 50
```

The count defaults to **50**. Any positive count is accepted, including 1 for a
preview. `medium` aliases `normal`; `progressive` aliases `incremental`.
`wildlife`, `wild-life`, and quoted `"wild life"` identify the same theme.
The installed command `crossword-book dogs easy 50` works the same way.

Each run creates a new directory under `dist/`. Existing output directories are
protected from replacement. Large books can take several minutes because each
grid must be solved consistently and fit its clues on one page.

### Large print

```sh
python crosswordgenerator.py dogs incremental 50 --edition large-print
```

| Edition | Grid | Clue text | Solutions |
| --- | --- | --- | --- |
| Standard | 9 × 9 easy, 11 × 11 normal, 13 × 13 hard | 8.5–10 points | Four per page |
| Large print | 8 × 8 at every level, at most 28 answers | **16–17 points** | Two per page, larger answer letters |

Large-print grids have larger writing squares, at least 28 points wide, and
fewer answers than normal standard grids. Difficulty still varies through word
familiarity and theme-clue style; it is a construction heuristic rather than a
human-calibrated rating. The large-print title page is labeled accordingly,
and its instructions use larger text. Small decorative captions and legal
credits are not subject to the clue-text minimum.

Incremental books move through three ordered stages: easy, normal, hard. A
50-puzzle book has 17 easy, 17 normal, and 16 hard puzzles, all in one theme.

### Repetition and clues

Every book prefers unused answers, especially unused theme answers. This is a
**strong preference, not a ban**: dense fully crossed grids still need some
common crossing words. Answers never repeat within a single puzzle, and exact
grids cannot repeat within a book. Use `--allow-repeats` to disable the across-
puzzle preference when you explicitly want unrestricted fill.

There are **1,265 theme entries across 11 themes**, at least 100 per theme, each with two clue
styles. The general bank includes **over 1,300 editorial clue overrides**. The
remaining dictionary clues are normalized into concise phrases; overlong or
unsuitable definitions are filtered out instead of cut off. General clues are
at most 72 characters; large-print crossing fill uses clues up to 52 characters.
Editorial overrides are loaded directly when the app starts—no rebuild needed.
These improvements reduce dictionary-like wording, but review a printed proof
and the clues before publishing a commercial edition.

### Multiple volumes

```sh
python crosswordgenerator.py dogs easy 50 --series "Dog Lovers"
python crosswordgenerator.py dogs easy 50 --series "Dog Lovers"
```

These create volumes 1 and 2. The volume appears on the title/copyright pages
and is saved in `book.json`. By default history is kept in
`.crossword-series/history.sqlite3`. Choose another history location with:

```sh
python crosswordgenerator.py dogs hard 50 --series "Dog Lovers" --history "my-series.sqlite3"
```

Reuse the **same series name and history file** for subsequent volumes. Names
are case-sensitive. Each series has one theme; different themes need distinct
series names. Difficulty and edition can change between volumes.

History remembers exact puzzle fingerprints, answer-use counts, and titles.
Exact puzzles and titles from previous volumes are excluded; previous answers
are penalized rather than absolutely forbidden. To repeat an earlier seed,
the history may therefore cause different fills. `--allow-repeats` cannot be
combined with `--series`.

The history file is local, not stored in GitHub. **Back it up when generation is
not running**, and keep it when moving to a different computer. Losing it loses
the cross-volume memory. Only completed books are recorded. A database lock
prevents two simultaneous jobs from taking the same volume number.

### Publishing details

```sh
python crosswordgenerator.py dogs incremental 50 --seed 42 --title "Dog Crossword Adventures" --publisher "Quickberry Books" --copyright-year 2026 --output dist/my-dog-book
```

Other options: `--subtitle`, `--edition`, `--series`, and `--history`.
`--seed` reproduces a book with the same code, banks, edition, repeat setting,
and prior series history. Without it the seed is random and saved in the JSON.

Every puzzle receives a distinct, theme-inspired title, also shown with its
solution. Titles are saved as `puzzles[].title`. Existing edited titles are
preserved when rendering a saved book.

## Interior and output

Each book contains:

1. A framed title page with theme motifs, crossword illustration, count, edition,
   difficulty, publisher, and series volume where applicable.
2. Copyright and crossword-specific How to Play pages.
3. One complete crossword **and all its clues per page**.
4. Solutions, dictionary credits, and a final thank-you page.

Theme answers have a **20% black gray fill** and starred clues (`*`). Solutions
retain the same shading. Generic answers remain unshaded except at crossings
with theme answers. No color conversion or external images are needed.

A 50-puzzle standard book has **68 pages**; a 50-puzzle large-print book has
**80 pages**. Solutions begin on page 54 in either edition. Interior printed
page numbers match physical PDF pages; title/copyright pages have no number.
All pages are US Letter, with side margins of at least 0.58 inches. A cover is
not included.

Each output folder contains:

- `book.pdf`: the complete print interior.
- `book.json`: seed, edition, titles, theme, settings, grids, clues, and series
  name/volume if selected.
- `wordlists/<theme>-easy.txt`, `<theme>-hard.txt`, and `used-answers.txt` in
  `ANSWER|clue` format.
- `licenses/`: dictionary source attribution and license texts.

## New reader niches

Five additional themes are available in both the desktop menu and terminal:

| Theme | Book focus | Example |
| --- | --- | --- |
| `gardening` | Plants, growing methods, tools, and garden crops | `python crosswordgenerator.py gardening easy 50` |
| `baking` | Ingredients, baking methods, breads, and pastries | `python crosswordgenerator.py baking medium 50` |
| `travel` | Journeys, destinations, capitals, and geography | `python crosswordgenerator.py travel incremental 50` |
| `space` | Astronomy, stars, planets, and spaceflight | `python crosswordgenerator.py space hard 50` |
| `christmas` | Festive traditions, decorations, foods, and Nativity | `python crosswordgenerator.py christmas easy 50` |

`astronomy` aliases `space`; `geography` and quoted `"travel and geography"`
alias `travel`; `xmas` aliases `christmas`. Add `--edition large-print` or a
`--series` name just as with the original themes. Each new theme has 120+ clue
pairs, 50 named puzzle titles plus additional generated titles, a book title and
subtitle, and its own grayscale vector motif.

See [THEME_NICHES.md](THEME_NICHES.md) for the intended audiences and seasonal
positioning. Current KDP sales and competition have not been verified.

## Editing content

Theme files in `crossword_book/data/<theme>.txt` use:

```text
ANSWER|straightforward clue|harder clue
```

Use unique uppercase ASCII answers without spaces. General editorial clues in
`fill-overrides.txt` use `ANSWER|clue`, with clues up to 72 characters. Restart
the app after editing. The bundled `fill.json` is the base dictionary; runtime
filters and editorial overrides select the usable fill.

Definitions originate from **Princeton WordNet 3.0**, under the included
`WORDNET-LICENSE.txt`. Word familiarity ratings use **wordfreq 3.1.1** by Robyn
Speer. Its code is Apache-2.0 and data is CC BY-SA 4.0; adapted frequency data
in `fill.json` remains CC BY-SA 4.0. Full credits and licenses are in
`crossword_book/data/` and accompany exported books.

To rebuild only the base dictionary (not required for generation), install
`wordfreq==3.1.1` and run:

```sh
python scripts/build_fill_bank.py /path/to/wordnet.zip
```

Use the official NLTK WordNet distribution recorded with a SHA-256 in
`fill.json`. TLS and checksum/signature verification should remain enabled.

## Validation and development

```sh
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
```

Checks cover crossings, numbering, symmetry, all themes and difficulties,
expanded banks, concise clues, repeat reduction, large-print font/grid sizes,
page fits, unique titles, history transactions, concurrent series access,
cancellation, output protection, and the desktop workflow. The desktop test
requires a display and skips itself on headless runs. On a Linux machine with
Xvfb installed, run `xvfb-run -a python -m unittest discover -s tests -v` to
exercise it as well.

The implementation checklist is in `IMPLEMENTATION_CHECKLIST.md`. Use the
existing isolated checkout; a separate worktree is unnecessary. Generated
books under `dist/` and default local series history are ignored by Git.
