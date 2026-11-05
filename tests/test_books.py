import contextlib
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from collections import defaultdict
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from crossword_book.core import THEMES, LEVELS, generate, make_book, slots_for, is_connected
from crossword_book.cli import main, normalize_theme
from crossword_book.pdf import write_pdf, draw_grid, register_fonts, PageFitError
from crossword_book.puzzle_titles import titles_for, assign_puzzle_titles


class CrosswordTests(unittest.TestCase):
    def assert_valid(self,puzzle):
        grid,entries = puzzle['grid'],puzzle['entries']
        size = 8 if puzzle.get('edition')=='large-print' else LEVELS[puzzle['difficulty']][0]
        self.assertEqual(len(grid),size)
        self.assertTrue(all(len(row)==size for row in grid))
        pattern = [''.join('.' if c else '#' for c in row) for row in grid]
        self.assertTrue(is_connected(pattern))
        white = {(r,c) for r,row in enumerate(grid) for c,char in enumerate(row) if char}
        self.assertGreaterEqual(len(white)/(size*size),.65)
        for r in range(size):
            for c in range(size):
                self.assertEqual(bool(grid[r][c]),bool(grid[size-1-r][size-1-c]))
        memberships = defaultdict(set)
        expected = set()
        for e in entries:
            dr,dc = (0,1) if e['direction']=='across' else (1,0)
            cells = tuple((e['row']+dr*i,e['col']+dc*i) for i in range(len(e['answer'])))
            self.assertEqual(''.join(grid[r][c] for r,c in cells),e['answer'])
            self.assertTrue(e['clue'])
            self.assertGreaterEqual(len(cells),3)
            expected.add((e['direction'],cells))
            for cell in cells:
                memberships[cell].add(e['direction'])
        self.assertEqual(set(memberships),white)
        self.assertTrue(all(directions=={'across','down'} for directions in memberships.values()))
        self.assertEqual(set(slots_for(pattern)),expected,'Every maximal run must have exactly one clue')
        self.assertEqual(len(entries),len(expected))
        self.assertEqual(len(entries),len({e['answer'] for e in entries}))
        starts = sorted({(e['row'],e['col']) for e in entries})
        for e in entries:
            self.assertEqual(e['number'],starts.index((e['row'],e['col']))+1)
        self.assertGreaterEqual(sum(e['themed'] and len(e['answer'])>=5 for e in entries),2)
        self.assertEqual(puzzle['checked_fraction'],1.0)

    def test_every_theme_and_level(self):
        for theme in THEMES:
            for level in LEVELS:
                with self.subTest(theme=theme,level=level):
                    self.assert_valid(generate(theme,level,random.Random(42)))

    def test_incremental_single_theme_and_reproducibility(self):
        book=make_book(3,'incremental','cats',seed=42)
        self.assertEqual(book,make_book(3,'incremental','cats',seed=42))
        self.assertEqual([p['difficulty'] for p in book['puzzles']],list(LEVELS))
        self.assertEqual({p['theme'] for p in book['puzzles']},{'cats'})
        self.assertEqual(len({str(p['grid']) for p in book['puzzles']}),3)

    def test_invalid_inputs(self):
        for count in [0,-1,1.5]:
            with self.assertRaises(ValueError):
                make_book(count)
        with self.assertRaises(ValueError):
            make_book(1,theme='dinosaurs')
        with self.assertRaises(ValueError):
            make_book(1,mode='expert')
        self.assertEqual(normalize_theme('wild life'),'wildlife')

    def test_distinct_titles_for_every_theme_and_long_books(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                titles=titles_for(theme,1000,42)
                self.assertEqual(len(titles),1000)
                self.assertEqual(len({title.casefold() for title in titles}),1000)
                self.assertEqual(titles,titles_for(theme,1000,42))
                self.assertNotEqual(titles[:50],titles_for(theme,50,43))
                self.assertTrue(all(title.casefold()!=theme for title in titles))

    def test_saved_book_titles_are_preserved_when_missing_titles_are_added(self):
        book={'theme':'dogs','seed':42,'puzzles':[{'title':'Paws and Play'},{},{}]}
        assign_puzzle_titles(book)
        self.assertEqual(book['puzzles'][0]['title'],'Paws and Play')
        self.assertEqual(len({p['title'] for p in book['puzzles']}),3)
        original=[p['title'] for p in book['puzzles']]
        assign_puzzle_titles(book)
        self.assertEqual(original,[p['title'] for p in book['puzzles']])
        with self.assertRaises(ValueError):
            assign_puzzle_titles({'theme':'dogs','puzzles':[{'title':'My Puzzle'},{'title':'MY PUZZLE'}]})

    def test_cli_and_output_protection(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'dogs'
            args=['dogs','easy','1','--seed','42','--copyright-year','2026','--output',str(output)]
            with contextlib.redirect_stdout(io.StringIO()):
                main(args)
            book=json.loads((output/'book.json').read_text())
            self.assert_valid(book['puzzles'][0])
            self.assertEqual(book['theme'],'dogs')
            self.assertTrue((output/'wordlists'/'used-answers.txt').is_file())
            self.assertTrue((output/'licenses'/'WORDNET-LICENSE.txt').is_file())
            before=(output/'book.pdf').read_bytes()
            pdf=PdfReader(output/'book.pdf')
            self.assertEqual(len(pdf.pages),7)
            self.assertEqual(book['publisher'],'Quirckberry Books')
            self.assertEqual(book['copyright_year'],2026)
            self.assertTrue(book['puzzles'][0]['title'])
            self.assertIn('DOG LOVERS CROSSWORDS',' '.join(pdf.pages[0].extract_text().split()))
            self.assertNotIn('LARGE PRINT',pdf.pages[0].extract_text())
            copyright_text=' '.join(pdf.pages[1].extract_text().split())
            self.assertIn('Copyright © 2026 Quirckberry Books.',copyright_text)
            self.assertIn('Third-party dictionary material',copyright_text)
            how_to=' '.join(pdf.pages[2].extract_text().split())
            self.assertIn('HOW TO PLAY',how_to)
            self.assertIn('Solutions begin on page 5.',how_to)
            self.assertIn('Solutions',pdf.pages[4].extract_text())
            self.assertIn('THANK YOU',pdf.pages[-1].extract_text())
            for page in pdf.pages:
                self.assertEqual(tuple(float(x) for x in page.mediabox),(0.,0.,612.,792.))
            text=' '.join(' '.join(page.extract_text().split()) for page in pdf.pages)
            for entry in book['puzzles'][0]['entries']:
                self.assertIn(' '.join(entry['clue'].split()),text)
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                main(args)
            self.assertEqual(before,(output/'book.pdf').read_bytes())

    def test_pdf_one_page_per_puzzle_at_every_level(self):
        book=make_book(3,'incremental','dogs',seed=42)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'book.pdf'
            write_pdf(book,path,'Single-page regression')
            pdf=PdfReader(path)
            # Three opening pages, three puzzles, solutions, credits, thank-you.
            self.assertEqual(len(pdf.pages),9)
            self.assertIn('Solutions begin on page 7.',' '.join(pdf.pages[2].extract_text().split()))
            self.assertIn('Solutions',pdf.pages[6].extract_text())
            for puzzle,page in zip(book['puzzles'],pdf.pages[3:6]):
                text=' '.join(page.extract_text().split())
                self.assertIn(f"Puzzle {puzzle['number']}:",text)
                self.assertIn(puzzle['title'],text)
                self.assertIn('ACROSS',text)
                self.assertIn('DOWN',text)
                self.assertNotIn('(continued)',text)
                self.assertIn('Shaded squares and * clues mark theme answers.',text)
                for entry in puzzle['entries']:
                    self.assertIn(' '.join(entry['clue'].split()),text)
                    if entry['themed']:
                        self.assertIn(f"*{entry['number']}.",text)
            solution_text=' '.join(pdf.pages[6].extract_text().split())
            for puzzle in book['puzzles']:
                self.assertIn(puzzle['title'],solution_text)

    def test_theme_squares_use_only_neutral_gray_in_puzzles_and_solutions(self):
        register_fonts()
        puzzle = {'grid':[list('CAT'),['O','','E'],list('WET')], 'entries':[
            dict(row=0,col=0,direction='across',answer='CAT',number=1,themed=True),
            dict(row=0,col=0,direction='down',answer='COW',number=1,themed=True),
            dict(row=2,col=0,direction='across',answer='WET',number=2,themed=False)]}
        expected = {(0,0),(0,1),(0,2),(1,0),(2,0)}
        stream=io.BytesIO()
        pdf_canvas=canvas.Canvas(stream)
        for solution in (False,True):
            draw_grid(pdf_canvas,puzzle,30,300,20,solution=solution)
            pdf_canvas.showPage()
        pdf_canvas.save()
        pdf=PdfReader(stream)
        for page in pdf.pages:
            shade,rectangle,seen=None,None,{}
            for operands,operator in page.get_contents().operations:
                self.assertNotIn(operator,(b'rg',b'RG'))
                if operator==b'g':
                    shade=float(operands[0])
                elif operator==b're':
                    rectangle=tuple(float(x) for x in operands)
                elif operator in (b'B',b'B*'):
                    x,y,_,_=rectangle
                    row,col=round((300-y)/20-1),round((x-30)/20)
                    seen[row,col]=shade
            self.assertEqual(len(seen),9)
            self.assertEqual({cell for cell,gray in seen.items() if gray==.8},expected)
            self.assertEqual(seen[1,1],0)
            self.assertEqual(seen[1,2],1)
            self.assertEqual(seen[2,1],1)

    def test_oversized_clues_never_add_pages_or_disappear(self):
        book=make_book(1,'easy','dogs',seed=42)
        for e in book['puzzles'][0]['entries']:
            e['clue'] = (e['clue']+' ')*8
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'book.pdf'
            with self.assertRaises(PageFitError):
                write_pdf(book,path,'Oversized clue regression')


if __name__=='__main__':
    unittest.main()
