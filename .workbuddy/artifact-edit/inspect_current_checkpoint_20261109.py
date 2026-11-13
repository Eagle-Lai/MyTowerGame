import sqlite3,sys,json
from pathlib import Path
p=Path(sys.argv[1]);c=sqlite3.connect(f'file:{p.as_posix()}?mode=ro',uri=True)
for name,sql in c.execute('select name,sql from sqlite_master'):
    if sql and sql.startswith('CREATE TABLE'):
        print(name,sql)
        for row in c.execute('select * from "'+name+'" limit 3'):
            print(str(row)[:2500])
c.close()
