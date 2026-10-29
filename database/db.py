import sqlite3, time, os
from config import DB_PATH

class DB:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        c = self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, is_premium INTEGER DEFAULT 0, expiry INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS apis (id INTEGER PRIMARY KEY AUTOINCREMENT, api_id TEXT, api_hash TEXT, phone TEXT, session_string TEXT, status TEXT DEFAULT 'active')")
        self.conn.commit()

    def upsert_user(self, uid, username, fname):
        self.conn.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))
        self.conn.commit()

    def is_premium(self, uid):
        r = self.conn.execute("SELECT is_premium, expiry FROM users WHERE user_id=?", (uid,)).fetchone()
        if r and r['is_premium'] == 1:
            if r['expiry'] == 0 or r['expiry'] > int(time.time()): return True
        return False
        
    def get_plan_info(self, uid):
        r = self.conn.execute("SELECT is_premium, expiry FROM users WHERE user_id=?", (uid,)).fetchone()
        if not r or r['is_premium'] == 0: return "Free Plan", "Unlimited (Restricted Limits)"
        if r['expiry'] == 0: return "Premium Plan", "Lifetime"
        return "Premium Plan", time.strftime('%Y-%m-%d', time.localtime(r['expiry']))

    def set_premium(self, uid, days):
        expiry = int(time.time()) + (days * 86400) if days > 0 else 0
        self.conn.execute("UPDATE users SET is_premium=1, expiry=? WHERE user_id=?", (expiry, uid))
        self.conn.commit()

    def get_apis(self): 
        return self.conn.execute("SELECT * FROM apis WHERE status='active'").fetchall()

    def add_api(self, api_id, api_hash, phone, session_string):
        self.conn.execute("INSERT INTO apis(api_id, api_hash, phone, session_string) VALUES(?,?,?,?)", (api_id, api_hash, phone, session_string))
        self.conn.commit()

    def has_session(self, user_id):
        return len(self.get_apis()) > 0

db = DB()
