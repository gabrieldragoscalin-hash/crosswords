"""US Letter interiors with one complete crossword and its clues per page."""
from pathlib import Path
from xml.sax.saxutils import escape
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from .frontmatter import opening_pages, thank_you_page, publication_details

THEME_CELL_GRAY = 0.80  # 20% black, independent of color-to-grayscale conversion.


def theme_cells(puzzle):
    """Union of the squares occupied by theme answers, including intersections."""
    cells = set()
    for entry in puzzle['entries']:
        if entry.get('themed', False):
            dr, dc = (0, 1) if entry['direction'] == 'across' else (1, 0)
            cells.update((entry['row']+dr*i, entry['col']+dc*i)
                         for i in range(len(entry['answer'])))
    return cells


def register_fonts():
    # ReportLab ships Bitstream Vera; embed it so PDFs render consistently offline.
    fonts = Path(reportlab.__file__).parent/'fonts'
    if 'Book' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('Book',str(fonts/'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('BookBold',str(fonts/'VeraBd.ttf')))
        pdfmetrics.registerFont(TTFont('BookItalic',str(fonts/'VeraIt.ttf')))
        pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='BookItalic')


def draw_grid(c,puzzle,x,top,cell,solution=False):
    numbers = {(p['row'],p['col']):p['number'] for p in puzzle['entries']}
    highlighted = theme_cells(puzzle)
    c.setLineWidth(.5)
    c.setStrokeGray(0)
    for r,row in enumerate(puzzle['grid']):
        for col,char in enumerate(row):
            px,py = x+col*cell,top-(r+1)*cell
            c.setFillGray((THEME_CELL_GRAY if (r,col) in highlighted else 1) if char else 0)
            c.rect(px,py,cell,cell,fill=1,stroke=1)
            if char:
                c.setFillGray(0)
                if not solution and (r,col) in numbers:
                    c.setFont('Book',max(4,cell*.26))
                    c.drawString(px+1.2,py+cell*.7,str(numbers[r,col]))
                if solution:
                    c.setFont('Book',cell*.63)
                    c.drawCentredString(px+cell/2,py+cell*.23,char)



class PageFitError(ValueError):
    """A puzzle cannot fit one page at the supported print sizes."""


def plan_puzzle(puzzle):
    """Measure all clues before drawing; never split, omit, or truncate one.

    One full-height clue column sits beside the grid; two further columns flow
    underneath it. Prefer larger type first, then the largest grid that fits.
    """
    register_fonts()
    blocks = []
    for direction in ('across', 'down'):
        entries = [e for e in puzzle['entries'] if e['direction'] == direction]
        if not entries:
            continue
        blocks.append((direction, True, direction.upper()))
        for entry in entries:
            marker = '*' if entry.get('themed', False) else ''
            text = f"<b>{marker}{entry['number']}.</b> {escape(entry['clue'])} ({len(entry['answer'])})"
            blocks.append((direction, False, text))
    size = len(puzzle['grid'])
    for font_size in (10, 9.5, 9, 8.5):
        body = ParagraphStyle('clue', fontName='Book', fontSize=font_size, leading=font_size*1.12)
        heading = ParagraphStyle('direction', fontName='BookBold', fontSize=font_size+1,
                                 leading=font_size+3)
        for desired_grid in (330, 312, 294, 276, 258, 240):
            side = min(desired_grid, size*32)
            regions = [(42,714,164), (224,714-side-16,164), (406,714-side-16,164)]
            drawn, index = [], 0
            for x, top, width in regions:
                y = top
                if index < len(blocks) and not blocks[index][1]:
                    continued = Paragraph(blocks[index][0].upper(), heading)
                    height = continued.wrap(width,700)[1]
                    y -= height
                    drawn.append((continued,x,y))
                    y -= 4
                while index < len(blocks):
                    _, is_heading, text = blocks[index]
                    para = Paragraph(text,heading if is_heading else body)
                    height = para.wrap(width,700)[1]
                    gap = 4 if is_heading else 2
                    needed = height
                    if is_heading and index+1 < len(blocks):
                        next_clue = Paragraph(blocks[index+1][2],body)
                        needed += gap+next_clue.wrap(width,700)[1]
                    if y-needed < 42:
                        break
                    y -= height
                    drawn.append((para,x,y))
                    y -= gap
                    index += 1
                if index == len(blocks):
                    return dict(grid_x=397-side/2,grid_top=714,cell=side/size,
                                font_size=font_size,clues=drawn)
    raise PageFitError('Clues cannot fit on one page at a readable size; shorten the clues or generate another grid')


def write_pdf(book,path,title):
    register_fonts()
    c = canvas.Canvas(str(path),pagesize=letter,invariant=1)
    c.setTitle(title)
    c.setAuthor(publication_details(book)[0])

    def footer(text):
        c.setFillColorRGB(0,0,0)
        c.setFont('Book',8)
        c.drawCentredString(306,30,text)
        c.drawRightString(570,30,str(c.getPageNumber()))

    opening_pages(c,book,title,draw_grid,footer)
    for puzzle in book['puzzles']:
        layout = plan_puzzle(puzzle)
        c.setFont('BookBold',17)
        c.drawString(42,744,f"Puzzle {puzzle['number']}: {puzzle['theme'].title()}")
        c.setFont('Book',10)
        c.drawRightString(570,744,puzzle['difficulty'].title())
        c.setFont('Book',8)
        c.drawString(42,727,'Shaded squares and * clues mark theme answers.')
        draw_grid(c,puzzle,layout['grid_x'],layout['grid_top'],layout['cell'])
        for para,x,y in layout['clues']:
            para.drawOn(c,x,y)
        footer(f"Puzzle {puzzle['number']} | {puzzle['difficulty'].title()}")
        c.showPage()
    for start in range(0,len(book['puzzles']),4):
        c.setFont('BookBold',17)
        c.drawString(54,744,'Solutions')
        for offset,puzzle in enumerate(book['puzzles'][start:start+4]):
            x,top = 54+(offset%2)*264,700-(offset//2)*320
            c.setFont('BookBold',10)
            c.drawString(x,top,f"{puzzle['number']}. {puzzle['theme'].title()}")
            rows,cols = len(puzzle['grid']),len(puzzle['grid'][0])
            cell = min(18,230/cols,270/rows)
            draw_grid(c,puzzle,x,top-16,cell,solution=True)
        footer(f'Solutions {start+1}-{min(start+4,len(book["puzzles"]))}')
        c.showPage()
    c.setFont('BookBold',17)
    c.drawString(54,744,'Dictionary credits')
    credits = (
        'General crossing-fill definitions are adapted from Princeton WordNet 3.0. '
        'Theme clues and editorial fill clues are supplied by this generator. '
        'Word familiarity rankings use wordfreq 3.1.1 by Robyn Speer '
        '(https://github.com/rspeer/wordfreq), whose data is available under '
        'Creative Commons Attribution-ShareAlike 4.0 '
        '(https://creativecommons.org/licenses/by-sa/4.0/). '
        'Sources include Google Books, Wikipedia, ParaCrawl, the Leeds Internet Corpus, '
        'OPUS OpenSubtitles 2018 / OpenSubtitles, and the freely available SUBTLEX '
        'data by Marc Brysbaert and colleagues. Changes: vocabulary selection, '
        'frequency rounding, inflections, clue shortening, and editorial overrides. '
        'Full source credits and license texts accompany the generated book.'
    )
    legal = (Path(__file__).parent/'data'/'WORDNET-LICENSE.txt').read_text()
    paragraphs = [credits]+[' '.join(p.split()) for p in legal.split('\n\n') if p.strip()]
    y=710
    style=ParagraphStyle('credits',fontName='Book',fontSize=8.5,leading=11)
    for text in paragraphs:
        p=Paragraph(escape(text),style)
        _,height=p.wrap(504,650)
        if y-height<54:
            footer('Dictionary credits')
            c.showPage()
            y=730
        y-=height
        p.drawOn(c,54,y)
        y-=10
    footer('Dictionary credits')
    c.showPage()
    thank_you_page(c,book,footer)
    c.showPage()
    c.save()
