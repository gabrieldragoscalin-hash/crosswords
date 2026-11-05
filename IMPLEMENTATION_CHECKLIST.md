# Book generator improvements

- [x] Expand all 11 theme banks: 1,265 entries, at least 100 per theme, with
  straightforward and harder clue pairs.
- [x] Prefer unused answers within a book. Reuse is penalized, with a gradual
  relaxation when dense crossings need common words; answers never repeat
  within a single puzzle.
- [x] Use shorter, more natural clues: 1,384 editorial overrides loaded at
  runtime, whole-definition filtering, and concise general crossing fill.
- [x] Add a large-print edition: fully checked 8 × 8 grids, at most 28 answers,
  clues of at least 16 points, larger writing squares, and two larger solutions
  per page. Standard single-page puzzles remain supported.
- [x] Track series volumes locally: completed-volume numbering, previous answer
  counts, strict exclusion of earlier exact puzzles and titles, database locks,
  and rollback on cancellation or export failure.
- [x] Add a desktop interface: theme/difficulty/edition controls, publishing
  details, series history selection, background generation, progress,
  cancellation, and buttons to open the PDF or output folder.

## Validation completed

- 23 automated tests passed, including the desktop test on a virtual display.
- All 11 themes exercised at all three difficulty levels in both editions.
- One 50-puzzle standard book verified at 68 US Letter pages.
- Two 50-puzzle large-print volumes verified at 80 US Letter pages each.
- Every clue checked on its own puzzle page; instructions point to the correct
  solution page; theme shading and starred clues retained.
- The two full series volumes contain 100 different puzzle grids and titles.
- Desktop responsiveness, generation, cancellation, and history rollback tested.
- Distribution wheel built with bundled content and both app launchers.

## Additional theme expansion

- [x] Gardening: 123 entries, garden artwork, book and puzzle titles.
- [x] Baking: 127 entries, whisk artwork, book and puzzle titles.
- [x] Travel and geography: 128 entries, compass artwork, book and puzzle titles.
- [x] Space and astronomy: 136 entries, planet artwork, book and puzzle titles.
- [x] Christmas: 138 entries, snowflake artwork, book and puzzle titles.
- [x] All new themes exposed in the desktop app and terminal, with friendly aliases.
- [x] Five full 50-puzzle sample books generated and verified, including standard
  and large-print layouts; all 250 puzzles retain every clue on one page.

Marketplace selection is audience-based. Live sales/rank/competition research
was blocked by the environment's network policy; no low-competition or revenue
claims are made.
