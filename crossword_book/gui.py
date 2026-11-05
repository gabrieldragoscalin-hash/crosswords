"""Tk desktop interface; generation runs off the UI thread."""
from datetime import datetime
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, font as tkfont
except ImportError:
    tk=None
from .core import THEMES
from .errors import GenerationCancelled
from .service import BookOptions, generate_book


class BookApp:
    def __init__(self,root):
        self.root=root
        root.title('Quirckberry Books - Crossword Generator')
        root.geometry('760x780');root.minsize(700,730)
        style=ttk.Style(root)
        if sys.platform!='win32' and 'clam' in style.theme_names():style.theme_use('clam')
        self.title_font=tkfont.nametofont('TkDefaultFont',root=root).copy()
        self.title_font.configure(size=19,weight='bold')
        self.events=queue.Queue();self.cancel_event=threading.Event()
        self.busy=False;self.last_output=None;self.closing=False
        defaults={'theme':'dogs','difficulty':'easy','count':'50','edition':'standard',
                  'publisher':'Quirckberry Books','year':str(datetime.now().year),
                  'seed':'','title':'','subtitle':'','series':'',
                  'history':str(Path('.crossword-series/history.sqlite3').resolve()),
                  'output':str(Path('dist').resolve())}
        self.values={k:tk.StringVar(root,value=v) for k,v in defaults.items()}
        self.avoid_repeats=tk.BooleanVar(root,value=True)
        self.status=tk.StringVar(root,value='Ready to create a book.')
        outer=ttk.Frame(root,padding=18);outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='Crossword Book Generator',font=self.title_font).pack(anchor='w')
        ttk.Label(outer,text='Themed books for black-and-white printing.').pack(anchor='w',pady=(2,12))
        main=ttk.LabelFrame(outer,text='Your book',padding=10);main.pack(fill='x')
        main.columnconfigure(1,weight=1);main.columnconfigure(3,weight=1)
        for row,(label,key,choices) in enumerate([
            ('Theme','theme',THEMES),('Difficulty','difficulty',('easy','medium','hard','incremental')),
            ('Edition','edition',('standard','large-print'))]):
            ttk.Label(main,text=label).grid(row=row,column=0,sticky='w',padx=4,pady=4)
            ttk.Combobox(main,textvariable=self.values[key],values=choices,state='readonly').grid(row=row,column=1,columnspan=3,sticky='ew',padx=4,pady=4)
        ttk.Label(main,text='Puzzles').grid(row=3,column=0,sticky='w',padx=4,pady=4)
        ttk.Spinbox(main,from_=1,to=10000,textvariable=self.values['count'],width=12).grid(row=3,column=1,sticky='w',padx=4,pady=4)
        ttk.Checkbutton(main,text='Prefer unused answers',variable=self.avoid_repeats).grid(row=3,column=2,columnspan=2,sticky='w')
        publishing=ttk.LabelFrame(outer,text='Publishing details',padding=10);publishing.pack(fill='x',pady=10)
        publishing.columnconfigure(1,weight=1)
        for row,(label,key) in enumerate([('Book title (optional)','title'),('Subtitle (optional)','subtitle'),
                                         ('Publisher','publisher'),('Copyright year','year'),('Seed (optional)','seed')]):
            ttk.Label(publishing,text=label).grid(row=row,column=0,sticky='w',padx=4,pady=3)
            ttk.Entry(publishing,textvariable=self.values[key]).grid(row=row,column=1,sticky='ew',padx=4,pady=3)
        series=ttk.LabelFrame(outer,text='Series (optional)',padding=10);series.pack(fill='x')
        series.columnconfigure(1,weight=1)
        ttk.Label(series,text='Series name').grid(row=0,column=0,sticky='w',padx=4,pady=3)
        ttk.Entry(series,textvariable=self.values['series']).grid(row=0,column=1,columnspan=2,sticky='ew',padx=4,pady=3)
        ttk.Label(series,text='Leave blank for a standalone book. Keep the history file for future volumes.').grid(row=1,column=0,columnspan=3,sticky='w',padx=4,pady=3)
        ttk.Label(series,text='History file').grid(row=2,column=0,sticky='w',padx=4,pady=3)
        ttk.Entry(series,textvariable=self.values['history']).grid(row=2,column=1,sticky='ew',padx=4,pady=3)
        ttk.Button(series,text='Browse...',command=self.choose_history).grid(row=2,column=2,padx=4)
        destination=ttk.Frame(outer);destination.pack(fill='x',pady=12);destination.columnconfigure(1,weight=1)
        ttk.Label(destination,text='Output folder').grid(row=0,column=0,padx=(0,8))
        ttk.Entry(destination,textvariable=self.values['output']).grid(row=0,column=1,sticky='ew')
        ttk.Button(destination,text='Browse...',command=self.choose_output).grid(row=0,column=2,padx=(8,0))
        actions=ttk.Frame(outer);actions.pack(fill='x')
        self.generate_button=ttk.Button(actions,text='Generate book',command=self.start);self.generate_button.pack(side='left')
        self.cancel_button=ttk.Button(actions,text='Cancel',command=self.cancel,state='disabled');self.cancel_button.pack(side='left',padx=8)
        self.open_button=ttk.Button(actions,text='Open PDF',command=lambda:self.open_path(self.last_output/'book.pdf'),state='disabled');self.open_button.pack(side='right')
        self.folder_button=ttk.Button(actions,text='Open folder',command=lambda:self.open_path(self.last_output),state='disabled');self.folder_button.pack(side='right',padx=8)
        self.progress=ttk.Progressbar(outer,mode='determinate');self.progress.pack(fill='x',pady=(12,6))
        ttk.Label(outer,textvariable=self.status,wraplength=700).pack(anchor='w')
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.poll_id=root.after(100,self.poll)

    def choose_output(self):
        path=filedialog.askdirectory(parent=self.root,title='Choose where to save books')
        if path:self.values['output'].set(path)

    def choose_history(self):
        path=filedialog.asksaveasfilename(parent=self.root,title='Choose or create a series history file',confirmoverwrite=False,defaultextension='.sqlite3',filetypes=[('Series history','*.sqlite3')])
        if path:self.values['history'].set(path)

    def options(self):
        v={k:value.get().strip() for k,value in self.values.items()}
        try:
            count=int(v['count']);year=int(v['year']);seed=int(v['seed']) if v['seed'] else None
        except ValueError:
            raise ValueError('Count, year, and seed must be whole numbers') from None
        if count<1:raise ValueError('Choose at least one puzzle')
        if not 1000<=year<=9999:raise ValueError('Copyright year must have four digits')
        if not v['publisher']:raise ValueError('Enter a publisher name')
        if not v['output']:raise ValueError('Choose an output folder')
        return BookOptions(theme=v['theme'],difficulty=v['difficulty'],count=count,edition=v['edition'],
                           seed=seed,title=v['title'] or None,subtitle=v['subtitle'] or None,
                           publisher=v['publisher'],copyright_year=year,output_parent=Path(v['output']),
                           avoid_repeats=self.avoid_repeats.get(),series=v['series'] or None,history=Path(v['history']))

    def start(self):
        if self.busy:return
        try:options=self.options()
        except ValueError as error:
            messagebox.showerror('Check your settings',str(error),parent=self.root);return
        self.busy=True;self.cancel_event.clear()
        self.generate_button.configure(state='disabled');self.cancel_button.configure(state='normal')
        self.open_button.configure(state='disabled');self.folder_button.configure(state='disabled')
        self.progress.configure(maximum=options.count,value=0)
        self.status.set('Generating crosswords...')
        def work():
            try:
                output=generate_book(options,progress=lambda done,total:self.events.put(('progress',(done,total))),cancel=self.cancel_event.is_set)
                self.events.put(('done',output))
            except GenerationCancelled:self.events.put(('cancelled',None))
            except Exception as error:self.events.put(('error',str(error)))
        self.worker=threading.Thread(target=work,daemon=True);self.worker.start()

    def cancel(self):
        self.cancel_event.set();self.cancel_button.configure(state='disabled');self.status.set('Cancelling...')

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='progress':
                    done,total=value;self.progress.configure(value=done)
                    self.status.set(f'Puzzle {done} of {total} complete. Preparing the PDF when all puzzles are ready...')
                else:
                    self.busy=False;self.generate_button.configure(state='normal');self.cancel_button.configure(state='disabled')
                    if kind=='done':
                        self.last_output=value;self.status.set(f'Book saved: {value}')
                        self.open_button.configure(state='normal');self.folder_button.configure(state='normal')
                    elif kind=='cancelled':self.status.set('Cancelled. No incomplete book was saved.')
                    else:
                        self.status.set('Generation failed. No incomplete book was saved.')
                        if not self.closing:messagebox.showerror('Unable to create book',value,parent=self.root)
        except queue.Empty:pass
        if self.closing and not self.busy:
            self.root.destroy();return
        self.poll_id=self.root.after(100,self.poll)

    def open_path(self,path):
        try:
            if sys.platform=='win32':os.startfile(str(path))
            else:subprocess.Popen(['open' if sys.platform=='darwin' else 'xdg-open',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except OSError as error:messagebox.showerror('Unable to open file',str(error),parent=self.root)

    def close(self):
        self.closing=True
        if self.busy:self.cancel()
        else:
            self.root.after_cancel(self.poll_id);self.root.destroy()


def main():
    if tk is None:
        print('Tkinter is required. On Linux install python3-tk; on Windows enable Tcl/Tk in the Python installer.',file=sys.stderr)
        return 1
    try:root=tk.Tk()
    except tk.TclError as error:
        print(f'Cannot open a desktop window: {error}',file=sys.stderr);return 1
    BookApp(root);root.mainloop();return 0


if __name__=='__main__':
    raise SystemExit(main())
