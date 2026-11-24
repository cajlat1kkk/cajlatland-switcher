import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3
import sys

def main():
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home()/".local/state"))/"cajlatland-switcher"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.umask(0o077)
    with sqlite3.connect(root/"exceptions.sqlite3") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS secret (id INTEGER PRIMARY KEY, salt BLOB)")
        conn.execute("CREATE TABLE IF NOT EXISTS ignored (digest BLOB PRIMARY KEY)")
        conn.execute("INSERT OR IGNORE INTO secret VALUES(1,?)", (secrets.token_bytes(32),))
        salt = conn.execute("SELECT salt FROM secret WHERE id=1").fetchone()[0]
        digest = hmac.digest(salt, sys.stdin.buffer.read(256).decode().casefold().encode(), hashlib.sha256)
        if sys.argv[1]=="reject":
            conn.execute("INSERT OR IGNORE INTO ignored VALUES(?)",(digest,))
        elif sys.argv[1]=="check":
            print("skip" if conn.execute("SELECT 1 FROM ignored WHERE digest=?",(digest,)).fetchone() else "ok",end="")
if __name__=="__main__":
    main()
