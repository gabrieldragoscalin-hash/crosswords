"""Branded, vector-only opening and closing pages for print interiors."""
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

DEFAULT_PUBLISHER = 'Quirckberry Books'
from .themes import TITLES, SUBTITLES, MOTIFS


def publication_details(book):
    return (book.get('publisher', DEFAULT_PUBLISHER),
            book.get('copyright_year', datetime.now(timezone.utc).year))


def motif(c, theme, x, y, size=18):
    """Draw original animal motifs as vectors, without external image assets."""
    c.saveState()
    c.translate(x,y)
    c.scale(size/20,size/20)
    c.setFillGray(0)
    c.setStrokeGray(0)
    kind=MOTIFS[theme]
    if kind == 'fish':
        c.ellipse(-8,-4,6,4,fill=1,stroke=0)
        p=c.beginPath(); p.moveTo(4,0); p.lineTo(11,5); p.lineTo(11,-5); p.close()
        c.drawPath(p,fill=1,stroke=0)
        c.setFillGray(1); c.circle(-4,1,0.8,fill=1,stroke=0)
    elif kind == 'feather':
        p=c.beginPath(); p.moveTo(-7,-7)
        p.curveTo(-6,6,2,12,8,9); p.curveTo(11,1,4,-6,-7,-7); p.close()
        c.drawPath(p,fill=1,stroke=0)
        c.setStrokeGray(1); c.setLineWidth(.7); c.line(-5,-5,6,7)
    elif kind == 'plant':
        c.setLineWidth(1.2);c.line(0,-9,0,5)
        for side in (-1,1):
            p=c.beginPath();p.moveTo(0,-1)
            p.curveTo(side*10,0,side*10,8,side*3,9)
            p.curveTo(side*1,7,side*1,3,0,-1);p.close()
            c.drawPath(p,fill=1,stroke=0)
    elif kind == 'whisk':
        c.setLineWidth(1.2);c.ellipse(-5,0,5,10,fill=0,stroke=1)
        c.line(0,-9,0,0)
        for side in (-1,1):
            p=c.beginPath();p.moveTo(0,0);p.curveTo(side*3,3,side*3,7,0,10)
            c.drawPath(p,fill=0,stroke=1)
    elif kind == 'compass':
        c.setLineWidth(1);c.circle(0,0,9,fill=0,stroke=1)
        p=c.beginPath();p.moveTo(0,8);p.lineTo(3,0);p.lineTo(0,-8);p.lineTo(-3,0);p.close()
        c.drawPath(p,fill=1,stroke=0)
        c.setFillGray(1)
        p=c.beginPath();p.moveTo(0,0);p.lineTo(0,-7);p.lineTo(-2.5,0);p.close()
        c.drawPath(p,fill=1,stroke=0)
    elif kind == 'planet':
        c.rotate(-20);c.circle(0,0,6,fill=1,stroke=0)
        c.setLineWidth(1.5);c.ellipse(-11,-3,11,3,fill=0,stroke=1)
        c.circle(-9,8,1,fill=1,stroke=0)
    elif kind == 'snowflake':
        c.setLineWidth(1.1)
        for angle in (0,60,120):
            c.saveState();c.rotate(angle);c.line(-9,0,9,0)
            for side in (-1,1):
                c.line(side*6,0,side*4,2);c.line(side*6,0,side*4,-2)
            c.restoreState()
    else:
        for tx,ty,rx,ry in [(-7,3,2.4,3.0),(-2.7,7,2.3,3.1),(2.7,7,2.3,3.1),(7,3,2.4,3.0)]:
            c.ellipse(tx-rx,ty-ry,tx+rx,ty+ry,fill=1,stroke=0)
        p=c.beginPath(); p.moveTo(-6,-6)
        p.curveTo(-10,-2,-5,1,-3,2); p.curveTo(-1,5,1,5,3,2)
        p.curveTo(5,1,10,-2,6,-6); p.curveTo(3,-8,2,-5,0,-5)
        p.curveTo(-2,-5,-3,-8,-6,-6); p.close()
        c.drawPath(p,fill=1,stroke=0)
    c.restoreState()


def frame(c):
    c.setStrokeGray(0)
    c.setLineWidth(1.8); c.rect(48,48,516,696,stroke=1,fill=0)
    c.setLineWidth(.6); c.rect(55,55,502,682,stroke=1,fill=0)


def paragraph(c,text,x,top,width,size=12,leading=None,font='Book',align=0,max_height=None):
    p=Paragraph(text,ParagraphStyle('front',fontName=font,fontSize=size,
                                  leading=leading or size*1.45,alignment=align))
    _,height=p.wrap(width,720)
    if max_height is not None and height>max_height:
        raise ValueError('Publication text is too long for the page; shorten the title, subtitle, or publisher name')
    p.drawOn(c,x,top-height)
    return top-height


def title_page(c,book,title,draw_grid):
    publisher,_=publication_details(book)
    large=book.get('edition')=='large-print'
    frame(c)
    for x in (226,266,306,346,386): motif(c,book['theme'],x,690,17)
    c.setFillGray(0)
    c.setFont('BookBold',8)
    c.drawCentredString(306,654,'L A R G E   P R I N T   E D I T I O N' if large else 'T H E M E D   C R O S S W O R D   C O L L E C T I O N')
    if book.get('volume'):
        c.setFont('BookBold',10); c.drawCentredString(306,634,f"VOLUME {book['volume']}")
    for size in (42,38,34,30,26):
        try:
            paragraph(c,escape(title.upper()),86,621,440,size=size,leading=size*1.12,
                      font='BookBold',align=1,max_height=143)
            break
        except ValueError:
            if size==26: raise
    c.setLineWidth(.8)
    divider=480 if large else 463
    c.line(110,divider,284,divider); c.line(328,divider,502,divider)
    motif(c,book['theme'],306,divider,15)
    subtitle=book.get('subtitle') or SUBTITLES[book['theme']]
    paragraph(c,escape(subtitle),86 if large else 96,455 if large else 441,440 if large else 420,
              size=16 if large else 12.5,leading=20 if large else None,font='BookItalic',align=1,max_height=40 if large else 44)
    c.setLineWidth(1)
    c.roundRect(206,217,200,190,10,stroke=1,fill=0)
    puzzle=book['puzzles'][0]
    cell=160/len(puzzle['grid'])
    draw_grid(c,puzzle,226,397,cell)
    c.setFont('Book',6.7)
    c.drawCentredString(306,226,'THEME WORDS SHADED')
    count=len(book['puzzles'])
    mode='EASY TO HARD' if book['mode']=='incremental' else ('MEDIUM' if book['mode']=='normal' else book['mode'].upper())
    badge=f'{count} {"PUZZLE" if count == 1 else "PUZZLES"}  |  {mode}  |  SOLUTIONS INCLUDED'
    c.roundRect(133,168,346,29,14,stroke=1,fill=0)
    c.setFont('BookBold',10 if large else 8.3)
    c.drawCentredString(306,178,badge)
    c.line(221,117,391,117)
    paragraph(c,escape(publisher.upper()),86,103,440,size=17,leading=20,
              font='BookBold',align=1,max_height=40)


def copyright_page(c,book):
    publisher,year=publication_details(book)
    name=escape(publisher)
    top=594
    texts=[
        f'Copyright © {year} {name}. All rights reserved in the original book design, editorial content, and compilation.',
        'No part of the original material may be reproduced, distributed, or transmitted without the publisher’s prior written permission, except for personal use of the puzzles by the purchaser or as permitted by law.',
        'Third-party dictionary material is used under its respective licenses. Attribution and license notices appear in Dictionary Credits at the back of this book. Those licenses govern that material.',
        *([f"Series: {escape(book['series'])}. Volume {book['volume']}."] if book.get('series') else []),
        'First edition.',
    ]
    for text in texts:
        top=paragraph(c,text,66,top,480,size=10,leading=15)-19


def how_to_page(c,book,footer):
    large=book.get('edition')=='large-print'
    size,leading=(16,23) if large else (11.5,17)
    c.setFont('BookBold',25); c.drawCentredString(306,716,'HOW TO PLAY')
    top=paragraph(c,'Use the clues and crossing letters to complete each grid.',
                  66,666,480,size=size,leading=leading)-22
    steps=[
        ('Follow the numbers.', 'Match each clue to its grid number. Across reads left to right; Down reads top to bottom.'),
        ('One square, one letter.', 'Write in white and shaded squares. Leave black squares empty. Omit spaces and punctuation.'),
        ('Use the crossings.', 'Each letter belongs to two answers. A letter you know can help you solve another clue.'),
        ('Spot the theme.', 'Gray squares mark theme answers; their clues start with *. Other answers are general crossing words.'),
        ('Check the length.', 'The number in parentheses is the answer length. If stuck, skip a clue and return later.'),
    ]
    for i,(heading,body) in enumerate(steps,1):
        top=paragraph(c,f'<b>{i}. {heading}</b> {body}',66,top,480,size=size,leading=leading)-16
    solution_page=len(book['puzzles'])+4
    paragraph(c,f'<b>Need a hand?</b> Solutions begin on page {solution_page}.',
              66,top-7,480,size=size,leading=leading)
    footer('How to Play')


def opening_pages(c,book,title,draw_grid,footer):
    title_page(c,book,title,draw_grid); c.showPage()
    copyright_page(c,book); c.showPage()
    how_to_page(c,book,footer); c.showPage()


def thank_you_page(c,book,footer):
    publisher,_=publication_details(book)
    large=book.get('edition')=='large-print'
    frame(c)
    for x in (266,306,346): motif(c,book['theme'],x,662,21)
    c.setFont('BookBold',34); c.drawCentredString(306,598,'THANK YOU')
    c.setLineWidth(.8); c.line(156,568,456,568)
    top=paragraph(c,f'Thank you for choosing <b>{escape(publisher)}</b>.',
                  96,530,420,size=15,leading=22,align=1)-26
    top=paragraph(c,'We hope these crosswords brought you a few discoveries, satisfying answers, and plenty of enjoyable puzzle time.',
                  106,top,400,size=16 if large else 13,leading=23 if large else 21,align=1)-31
    top=paragraph(c,'Keep your curiosity sharp.<br/>There is always another clue to explore.',
                  106,top,400,size=16 if large else 13,leading=23 if large else 21,font='BookItalic',align=1)-40
    paragraph(c,'If you enjoyed this book, an honest review can help other puzzle lovers discover it.',
              116,top,380,size=16 if large else 11,leading=23 if large else 18,align=1)
    c.setLineWidth(.8); c.line(221,143,391,143)
    paragraph(c,escape(publisher.upper()),86,126,440,size=17,leading=20,
              font='BookBold',align=1,max_height=40)
    # Keep the final frame uncluttered; the interior pages carry page numbers.
