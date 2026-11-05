from pathlib import Path
import re
import tempfile
import unittest
from pypdf import PdfReader
from crossword_book.core import THEMES,load_entries,make_book
from crossword_book.themes import TITLES,SUBTITLES,MOTIFS
from crossword_book.cli import normalize_theme
from crossword_book.pdf import write_pdf
from crossword_book.puzzle_titles import titles_for

NEW_THEMES=('gardening','baking','travel','space','christmas')


class NewThemeTests(unittest.TestCase):
    def test_catalog_has_five_complete_new_niches(self):
        self.assertGreaterEqual(len(THEMES),11)
        self.assertTrue(set(NEW_THEMES)<=set(THEMES))
        for theme in NEW_THEMES:
            with self.subTest(theme=theme):
                self.assertTrue(TITLES[theme]);self.assertTrue(SUBTITLES[theme])
                self.assertNotEqual(MOTIFS[theme],'paw')
                entries=load_entries(theme)
                self.assertGreaterEqual(len(entries),100)
                for entry in entries:
                    for clue in (entry.easy,entry.hard):
                        self.assertNotRegex(clue,re.compile(r'\b'+re.escape(entry.answer)+r'\b',re.I))
                titles=titles_for(theme,50,42)
                self.assertEqual(len(set(titles)),50)

    def test_friendly_theme_aliases(self):
        for value,theme in [('astronomy','space'),('geography','travel'),('travel and geography','travel'),('xmas','christmas')]:
            self.assertEqual(normalize_theme(value),theme)

    def test_all_new_theme_interiors_in_both_editions(self):
        with tempfile.TemporaryDirectory() as temporary:
            for theme in NEW_THEMES:
                for edition in ('standard','large-print'):
                    with self.subTest(theme=theme,edition=edition):
                        book=make_book(1,'normal',theme,42,edition=edition)
                        path=Path(temporary)/f'{theme}-{edition}.pdf'
                        write_pdf(book,path,TITLES[theme])
                        pdf=PdfReader(path)
                        self.assertEqual(len(pdf.pages),7)
                        self.assertIn(TITLES[theme].upper(),' '.join(pdf.pages[0].extract_text().split()))
                        self.assertIn('HOW TO PLAY',pdf.pages[2].extract_text())
                        self.assertIn('THANK YOU',pdf.pages[-1].extract_text())
                        puzzle=book['puzzles'][0]
                        text=' '.join(pdf.pages[3].extract_text().split())
                        self.assertIn(puzzle['title'],text)
                        for entry in puzzle['entries']:
                            self.assertIn(' '.join(entry['clue'].split()),text)
                            if entry['themed']:self.assertIn(f"*{entry['number']}.",text)


if __name__=='__main__':unittest.main()
