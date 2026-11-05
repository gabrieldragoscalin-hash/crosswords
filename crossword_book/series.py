"""Local, transactional series history. No external service is required."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from .core import grid_signature


class SeriesSession:
    def __init__(self,path,name,theme):
        self.path=Path(path)
        self.name=name.strip()
        if not self.name: raise ValueError('Series name cannot be empty')
        self.theme=theme
        self.connection=None
        self.usage=Counter(); self.grids=set(); self.titles=set(); self.volume=1

    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        db=sqlite3.connect(self.path,timeout=1,isolation_level=None)
        self.connection=db
        try:
            db.execute('CREATE TABLE IF NOT EXISTS crossword_volumes (series TEXT NOT NULL, volume INTEGER NOT NULL, theme TEXT NOT NULL, created_at TEXT NOT NULL, output_path TEXT NOT NULL, manifest TEXT NOT NULL, PRIMARY KEY(series,volume))')
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute('SELECT volume,theme,manifest FROM crossword_volumes WHERE series=? ORDER BY volume',(self.name,)).fetchall()
            for volume,theme,raw in rows:
                if theme!=self.theme:
                    raise ValueError('This series already uses a different theme; choose a new series name')
                saved=json.loads(raw)
                self.volume=max(self.volume,volume+1)
                self.usage.update(saved['answers'])
                self.grids.update(saved['grids'])
                self.titles.update(saved['titles'])
            return self
        except BaseException:
            db.close();self.connection=None
            raise

    def record(self,book,output):
        manifest=dict(answers=dict(Counter(e['answer'] for p in book['puzzles'] for e in p['entries'])),
                      grids=[grid_signature(p['grid']) for p in book['puzzles']],
                      titles=[p['title'] for p in book['puzzles']],seed=book['seed'],
                      edition=book['edition'],mode=book['mode'])
        self.connection.execute('INSERT INTO crossword_volumes VALUES (?,?,?,?,?,?)',
            (self.name,self.volume,self.theme,datetime.now(timezone.utc).isoformat(),
             str(Path(output).resolve()),json.dumps(manifest,sort_keys=True)))

    def commit(self):
        self.connection.execute('COMMIT')

    def __exit__(self,*exc):
        if self.connection is not None:
            self.connection.close()  # An uncommitted transaction rolls back.
