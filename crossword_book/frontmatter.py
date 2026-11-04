"""Branded, vector-only opening and closing pages for print interiors."""
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

DEFAULT_PUBLISHER = 'Quickberry Books'
TITLES = {
    'dogs': 'Dog Lovers Crosswords', 'cats': 'Cat Lovers Crosswords',
    'wildlife': 'Wildlife Crosswords', 'animals': 'Animal Lovers Crosswords',
    'birds': 'Bird Lovers Crosswords', 'fish': 'Fish Lovers Crosswords',
}
SUBTITLES = {
    'dogs': 'Tail-wagging fun, one clue at a time.',
    'cats': 'Purr-fect puzzles for curious minds.',
    'wildlife': 'Explore the wild, one clue at a time.',
    'animals': 'A world of animals, one clue at a time.',
    'birds': 'Let your curiosity take flight.',
    'fish': 'Dive into a fresh crossword challenge.',
}


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
    if theme == 'fish':
        c.ellipse(-8,-4,6,4,fill=1,stroke=0)
        p=c.beginPath(); p.moveTo(4,0); p.lineTo(11,5); p.lineTo(11,-5); p.close()
        c.drawPath(p,fill=1,stroke=0)
        c.setFillGray(1); c.circle(-4,1,0.8,fill=1,stroke=0)
    elif theme == 'birds':
        p=c.beginPath(); p.moveTo(-7,-7)
        p.curveTo(-6,6,2,12,8,9); p.curveTo(11,1,4,-6,-7,-7); p.close()
        c.drawPath(p,fill=1,stroke=0)
        c.setStrokeGray(1); c.setLineWidth(.7); c.line(-5,-5,6,7)
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
    frame(c)
    for x in (226,266,306,346,386): motif(c,book['theme'],x,690,17)
    c.setFillGray(0)
    c.setFont('BookBold',8)
    c.drawCentredString(306,654,'T H E M E D   C R O S S W O R D   C O L L E C T I O N')
    for size in (42,38,34,30,26):
        try:
            paragraph(c,escape(title.upper()),86,621,440,size=size,leading=size*1.12,
                      font='BookBold',align=1,max_height=143)
            break
        except ValueError:
            if size==26: raise
    c.setLineWidth(.8)
    c.line(110,463,284,463); c.line(328,463,502,463)
    motif(c,book['theme'],306,463,15)
    subtitle=book.get('subtitle') or SUBTITLES[book['theme']]
    paragraph(c,escape(subtitle),96,441,420,size=12.5,font='BookItalic',align=1,max_height=44)
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
    c.setFont('BookBold',8.3)
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
        'First edition.',
    ]
    for text in texts:
        top=paragraph(c,text,66,top,480,size=10,leading=15)-19


def how_to_page(c,book,footer):
    c.setFont('BookBold',25); c.drawCentredString(306,716,'HOW TO PLAY')
    top=paragraph(c,'A little curiosity and a few crossing letters can go a long way.',
                  66,666,480,size=12,leading=18)-23
    steps=[
        ('Follow the numbers.', 'Match a clue’s number to the small number in the grid. Across answers read left to right; Down answers read top to bottom.'),
        ('One square, one letter.', 'Write in the white and shaded squares. Leave black squares empty. Answers have no spaces or punctuation.'),
        ('Let the crossings help.', 'Every letter belongs to both an Across answer and a Down answer. Use letters you already know to solve another clue.'),
        ('Spot the theme answers.', 'Light gray squares belong to answers about this book’s theme. Their clues begin with an asterisk (*). Other answers provide general English crossing words.'),
        ('Check the answer length.', 'The number in parentheses after each clue tells you how many letters to write. If you get stuck, try another clue and come back later.'),
    ]
    for i,(heading,body) in enumerate(steps,1):
        top=paragraph(c,f'<b>{i}. {heading}</b> {body}',66,top,480,size=11.5,leading=17)-17
    solution_page=len(book['puzzles'])+4
    paragraph(c,f'<b>Need a hand?</b> Solutions begin on page {solution_page}.',
              66,top-7,480,size=12,leading=18)
    footer('How to Play')


def opening_pages(c,book,title,draw_grid,footer):
    title_page(c,book,title,draw_grid); c.showPage()
    copyright_page(c,book); c.showPage()
    how_to_page(c,book,footer); c.showPage()


def thank_you_page(c,book,footer):
    publisher,_=publication_details(book)
    frame(c)
    for x in (266,306,346): motif(c,book['theme'],x,662,21)
    c.setFont('BookBold',34); c.drawCentredString(306,598,'THANK YOU')
    c.setLineWidth(.8); c.line(156,568,456,568)
    top=paragraph(c,f'Thank you for choosing <b>{escape(publisher)}</b>.',
                  96,530,420,size=15,leading=22,align=1)-26
    top=paragraph(c,'We hope these crosswords brought you a few discoveries, satisfying answers, and plenty of enjoyable puzzle time.',
                  106,top,400,size=13,leading=21,align=1)-31
    top=paragraph(c,'Keep your curiosity sharp.<br/>There is always another clue to explore.',
                  106,top,400,size=13,leading=21,font='BookItalic',align=1)-40
    paragraph(c,'If you enjoyed this book, an honest review can help other puzzle lovers discover it.',
              116,top,380,size=11,leading=18,align=1)
    c.setLineWidth(.8); c.line(221,143,391,143)
    paragraph(c,escape(publisher.upper()),86,126,440,size=17,leading=20,
              font='BookBold',align=1,max_height=40)
    # Keep the final frame uncluttered; the interior pages carry page numbers.
