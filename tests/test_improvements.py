from collections import Counter
from dataclasses import replace
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pypdf import PdfReader
from crossword_book.clues import fill_records,natural_clue
from crossword_book.core import THEMES,LEVELS,load_entries,make_book,grid_signature
from crossword_book.errors import GenerationCancelled
from crossword_book.pdf import plan_puzzle,write_pdf
from crossword_book.series import SeriesSession
from crossword_book.service import BookOptions,generate_book
import test_books


class ImprovementTests(unittest.TestCase):
    def test_expanded_theme_banks_and_concise_fill(self):
        for theme in THEMES:
            entries=load_entries(theme)
            self.assertGreaterEqual(len(entries),100)
            self.assertEqual(len(entries),len({e.answer for e in entries}))
        records=fill_records()
        self.assertGreater(len(records),10000)
        self.assertTrue(all(len(r[0])<=72 for r in records.values()))
        self.assertEqual(records['BOOK'][0],'Bound collection of pages')
        self.assertEqual(natural_clue('A person who guides visitors'),'One who guides visitors')
        self.assertIsNone(natural_clue('A very long definition '+('with details '*20)))
        self.assertIsNone(natural_clue('Surgical removal of tissue'))

    def test_repeat_avoidance_reduces_reused_answers(self):
        def repeats(book):
            counts=Counter(e['answer'] for p in book['puzzles'] for e in p['entries'])
            return sum(n-1 for n in counts.values())
        unrestricted=make_book(12,'easy','dogs',42,avoid_repeats=False)
        balanced=make_book(12,'easy','dogs',42)
        self.assertLess(repeats(balanced),repeats(unrestricted))

    def test_large_print_all_themes_and_levels(self):
        validator=test_books.CrosswordTests()
        for theme in THEMES:
            for level in LEVELS:
                with self.subTest(theme=theme,level=level):
                    puzzle=make_book(1,level,theme,42,edition='large-print')['puzzles'][0]
                    validator.assert_valid(puzzle)
                    self.assertLessEqual(len(puzzle['entries']),28)
                    layout=plan_puzzle(puzzle)
                    self.assertGreaterEqual(layout['font_size'],16)
                    self.assertGreaterEqual(layout['cell'],28)

    def test_large_print_pdf_sizes_and_answer_pages(self):
        book=make_book(3,'incremental','dogs',42,edition='large-print')
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'large.pdf';write_pdf(book,path,'Large Print Test')
            pdf=PdfReader(path)
            self.assertEqual(len(pdf.pages),10)
            self.assertIn('L A R G E',pdf.pages[0].extract_text())
            self.assertIn('Solutions begin on page 7.',' '.join(pdf.pages[2].extract_text().split()))
            for puzzle,page in zip(book['puzzles'],pdf.pages[3:6]):
                text=' '.join(page.extract_text().split())
                for entry in puzzle['entries']:
                    self.assertIn(' '.join(entry['clue'].split()),text)
            sizes=[]
            pdf.pages[6].extract_text(visitor_text=lambda text,cm,tm,font,size:sizes.append(size) if text.strip().isalpha() and len(text.strip())==1 else None)
            self.assertTrue(sizes)
            self.assertGreaterEqual(min(sizes),16)

    def test_large_print_label_cannot_be_added_to_standard_grids(self):
        book=make_book(1,'easy','dogs',42)
        book['edition']='large-print'
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):write_pdf(book,Path(d)/'invalid.pdf','Invalid edition')

    def test_generation_remains_possible_with_heavy_prior_usage(self):
        first=make_book(8,'easy','dogs',42,edition='large-print')
        usage=Counter(e['answer'] for p in first['puzzles'] for e in p['entries'])
        excluded={grid_signature(p['grid']) for p in first['puzzles']}
        following=make_book(2,'easy','dogs',42,edition='large-print',
                            prior_usage={w:n*20 for w,n in usage.items()},excluded_grids=excluded)
        self.assertEqual(len(following['puzzles']),2)
        self.assertFalse(excluded & {grid_signature(p['grid']) for p in following['puzzles']})

    def test_series_remembers_volumes_answers_grids_and_titles(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            options=BookOptions(count=2,seed=42,edition='large-print',series='Pawprint Adventures',history=root/'history.sqlite3')
            first=generate_book(replace(options,output=root/'one'))
            second=generate_book(replace(options,output=root/'two'))
            a=json.loads((first/'book.json').read_text());b=json.loads((second/'book.json').read_text())
            self.assertEqual((a['volume'],b['volume']),(1,2))
            self.assertFalse({grid_signature(p['grid']) for p in a['puzzles']} & {grid_signature(p['grid']) for p in b['puzzles']})
            self.assertFalse({p['title'] for p in a['puzzles']} & {p['title'] for p in b['puzzles']})
            with SeriesSession(options.history,options.series,'dogs') as history:
                self.assertEqual(history.volume,3)
                self.assertEqual(len(history.grids),4)
                self.assertEqual(sum(history.usage.values()),sum(len(p['entries']) for book in (a,b) for p in book['puzzles']))
            with self.assertRaises(ValueError):
                generate_book(replace(options,theme='cats',output=root/'wrong-theme'))
            with self.assertRaises(ValueError):
                generate_book(replace(options,output=first))

    def test_cancellation_and_failed_pdf_leave_no_book_or_history_volume(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);options=BookOptions(count=3,seed=42,edition='large-print',series='Rollback',history=root/'history.sqlite3',output=root/'cancelled')
            event=threading.Event()
            with self.assertRaises(GenerationCancelled):
                generate_book(options,progress=lambda done,total:event.set(),cancel=event.is_set)
            self.assertFalse(options.output.exists())
            with patch('crossword_book.service.write_pdf',side_effect=ValueError('Render failed')):
                with self.assertRaises(ValueError):generate_book(replace(options,count=1))
            with patch.object(SeriesSession,'commit',side_effect=sqlite3.OperationalError('Commit failed')):
                with self.assertRaises(sqlite3.OperationalError):generate_book(replace(options,count=1))
            self.assertFalse(options.output.exists())
            with SeriesSession(options.history,options.series,'dogs') as history:
                self.assertEqual(history.volume,1)
                self.assertFalse(history.grids)

    def test_cancelled_before_start_and_invalid_settings(self):
        with tempfile.TemporaryDirectory() as d:
            base=BookOptions(output=Path(d)/'book')
            with self.assertRaises(GenerationCancelled):generate_book(base,cancel=lambda:True)
            for option in [replace(base,count=0),replace(base,edition='tiny'),replace(base,publisher=''),replace(base,copyright_year=0),replace(base,series='X',avoid_repeats=False)]:
                with self.assertRaises(ValueError):generate_book(option)
            self.assertFalse(base.output.exists())

    def test_series_lock_prevents_two_simultaneous_volumes(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'history.sqlite3'
            with SeriesSession(path,'Locked','dogs'):
                with self.assertRaises(sqlite3.OperationalError):
                    with SeriesSession(path,'Locked','dogs'):pass


@unittest.skipUnless(os.environ.get('DISPLAY'),'Requires a desktop or virtual X display')
class DesktopTests(unittest.TestCase):
    def test_generate_and_cancel_from_desktop(self):
        from crossword_book.gui import BookApp,tk
        if tk is None:self.skipTest('Tkinter unavailable')
        with tempfile.TemporaryDirectory() as d:
            root=tk.Tk();app=BookApp(root);root.withdraw()
            errors=[]
            with patch('crossword_book.gui.messagebox.showerror',side_effect=lambda *a,**k:errors.append(a)):
                for name,value in {'theme':'fish','difficulty':'medium','edition':'large-print','count':'1','seed':'42','series':'Desktop Demo','history':str(Path(d)/'history.sqlite3'),'output':d}.items():app.values[name].set(value)
                ticks=[]
                root.after(1,lambda:ticks.append('responsive'))
                app.start();deadline=time.monotonic()+30
                while app.busy and time.monotonic()<deadline:root.update();time.sleep(.01)
                self.assertFalse(app.busy);self.assertFalse(errors);self.assertTrue(ticks)
                self.assertTrue((app.last_output/'book.pdf').is_file())
                saved=json.loads((app.last_output/'book.json').read_text())
                self.assertEqual((saved['theme'],saved['edition'],saved['volume']),('fish','large-print',1))
                app.values['count'].set('50');app.start();root.after(10,app.cancel)
                deadline=time.monotonic()+30
                while app.busy and time.monotonic()<deadline:root.update();time.sleep(.01)
                self.assertFalse(app.busy);self.assertFalse(errors)
                self.assertIn('Cancelled',app.status.get())
                with SeriesSession(Path(d)/'history.sqlite3','Desktop Demo','fish') as history:self.assertEqual(history.volume,2)
                app.close()


if __name__=='__main__':unittest.main()
