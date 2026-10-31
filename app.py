#!/usr/bin/env python3
"""
VaultCore Bank - Intentionally vulnerable training app (CTF lab).
DO NOT expose to the internet. Localhost practice target only.
"""
import base64
import hashlib
import hmac
import json
import os
import sqlite3
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "vaultcore.db")
JWT_SECRET = "vcore_sup3r_s3cr3t_2024"  # session signing key

PORT = 1337


# ---------------------------------------------------------------- db setup
def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    if os.path.exists(DB):
        return
    con = sqlite3.connect(DB)
    c = con.cursor()
    c.execute("""CREATE TABLE users(
        id INTEGER PRIMARY KEY, username TEXT, password TEXT,
        role TEXT, fullname TEXT, private_note TEXT)""")
    c.execute("""CREATE TABLE transactions(
        id INTEGER PRIMARY KEY, user_id INTEGER,
        description TEXT, amount TEXT)""")
    c.execute("""CREATE TABLE secrets(
        id INTEGER PRIMARY KEY, k TEXT, v TEXT)""")
    c.execute("""CREATE TABLE guestbook(
        id INTEGER PRIMARY KEY, author TEXT, message TEXT)""")

    md5 = lambda s: hashlib.md5(s.encode()).hexdigest()
    users = [
        (1, "alice",   md5("winter2024"),          "user",  "Alice Ferri",
         "Promemoria: rinnovare carta a marzo."),
        (2, "bob",     md5("bobspassword"),        "user",  "Bob Rinaldi",
         "PIN bancomat: non scriverlo qui!"),
        (3, "carla",   md5("carla!banking"),       "user",  "Carla Neri",
         "Chiedere aumento limite bonifici."),
        (4, "sysadmin", md5("xQ9!mV2#pL7zR"),      "user",  "Sist. Amministratore",
         "FLAG{1d0r_pr1v_3sc4l4t10n} - nota interna, non condividere."),
        (5, "vcore_admin", md5("Zt#8wLp!42xQnK"),  "admin", "Amministratore VaultCore",
         "Chiave di failover nel caveau B."),
    ]
    c.executemany("INSERT INTO users VALUES(?,?,?,?,?,?)", users)

    txs = [
        (1, 1, "Stipendio ottobre", "+2450.00"),
        (2, 1, "Affitto", "-850.00"),
        (3, 1, "Spesa supermercato", "-132.40"),
        (4, 2, "Ricarica telefono", "-20.00"),
        (5, 2, "Bonifico a Carla", "-300.00"),
        (6, 3, "Bonifico da Bob", "+300.00"),
        (7, 4, "Manutenzione server", "-1200.00"),
        (8, 5, "Audit sicurezza Q3", "-5600.00"),
    ]
    c.executemany("INSERT INTO transactions VALUES(?,?,?,?)", txs)

    secrets = [
        (1, "api_key_mobile", "ak_live_9f2kLq7TzXwP"),
        (2, "flag3", "FLAG{un10n_sql_3xtr4ct10n}"),
        (3, "note", "le credenziali di deploy sono nel backup"),
    ]
    c.executemany("INSERT INTO secrets VALUES(?,?,?)", secrets)

    c.execute("INSERT INTO guestbook(author,message) VALUES(?,?)",
              ("alice", "Ottimo servizio, finalmente una banca moderna!"))
    con.commit()
    con.close()


def q(sql):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    rows = cur.execute(sql).fetchall()
    con.close()
    return rows


# ------------------------------------------------------------- session jwt
def b64e(b): return base64.urlsafe_b64encode(b).decode().rstrip("=")
def b64d(s):
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def make_session(username, role):
    payload = b64e(json.dumps({"u": username, "role": role}).encode())
    sig = b64e(hmac.new(JWT_SECRET.encode(), payload.encode(),
                       hashlib.sha256).digest())
    return f"{payload}.{sig}"


def read_session(token):
    try:
        payload, sig = token.split(".")
        expect = b64e(hmac.new(JWT_SECRET.encode(), payload.encode(),
                               hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expect):
            return None
        return json.loads(b64d(payload))
    except Exception:
        return None


# ------------------------------------------------------------------- pages
LAYOUT = """<!doctype html><html><head><meta charset=utf-8>
<title>VaultCore Bank</title><style>
body{{background:#0b0f14;color:#c9d4de;font-family:Consolas,monospace;
margin:0;padding:0}}
a{{color:#4ec9b0}} .wrap{{max-width:860px;margin:40px auto;padding:0 20px}}
header{{background:#101820;padding:18px 0;border-bottom:1px solid #1e2b38}}
header .wrap{{margin:0 auto;display:flex;justify-content:space-between}}
h1{{color:#4ec9b0;font-size:20px;margin:0}}
.card{{background:#101820;border:1px solid #1e2b38;border-radius:6px;
padding:22px;margin:20px 0}}
input,textarea{{background:#0b0f14;border:1px solid #2a3a48;color:#c9d4de;
padding:9px;width:100%;box-sizing:border-box;margin:6px 0;font-family:inherit}}
button{{background:#4ec9b0;color:#06121a;border:0;padding:10px 22px;
cursor:pointer;font-weight:bold;font-family:inherit}}
table{{width:100%;border-collapse:collapse}}td,th{{border:1px solid #1e2b38;
padding:8px;text-align:left}}
.flag{{color:#ffd700;font-weight:bold}}
.warn{{color:#e06c75;font-size:13px}}
pre{{background:#0b0f14;padding:12px;overflow:auto;border:1px solid #1e2b38}}
</style></head><body>
<header><div class=wrap><h1>&#127974; VaultCore Bank</h1>
<nav>{nav}</nav></div></header>
<div class=wrap>{body}</div></body></html>"""


def nav(sess):
    if sess:
        return (f"<a href=/dashboard>Conto</a> | <a href=/account>Profilo</a> | "
                f"<a href=/search>Movimenti</a> | <a href=/guestbook>Guestbook</a> | "
                f"<a href=/download?file=estratto_conto.pdf>Estratto</a> | "
                f"<a href=/admin>Admin</a> | <a href=/logout>Esci ({sess['u']})</a>")
    return ("<a href=/>Home</a> | <a href=/login>Accedi</a> | "
            "<a href=/guestbook>Guestbook</a>")


def page(sess, body):
    return LAYOUT.format(nav=nav(sess), body=body).encode()


# ---------------------------------------------------------------- handler
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def sess(self):
        c = self.headers.get("Cookie", "")
        for part in c.split(";"):
            if part.strip().startswith("session="):
                return read_session(part.strip()[8:])
        return None

    def send(self, data, code=200, ctype="text/html; charset=utf-8",
             cookie=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(data if isinstance(data, bytes) else data.encode())

    def params(self):
        u = urllib.parse.urlparse(self.path)
        get = urllib.parse.parse_qs(u.query)
        post = {}
        if self.command == "POST":
            n = int(self.headers.get("Content-Length", 0))
            post = urllib.parse.parse_qs(self.rfile.read(n).decode())
        f = lambda d, k, dft="": d.get(k, [dft])[0]
        return u.path, get, post, f

    def do_GET(self):
        path, get, post, f = self.params()
        s = self.sess()

        if path == "/":
            self.send(page(s, """<div class=card><h2>Benvenuto in VaultCore</h2>
<p>La banca digitale dei professionisti. Sicurezza certificata ISO-27001*.</p>
<p class=warn>* certificazione in fase di rinnovo</p>
<p><a href=/login>&raquo; Area clienti</a></p></div>
<div class=card><h3>Servizi</h3><ul><li>Conto corrente 4.0</li>
<li>Bonifici istantanei</li><li>Trading</li></ul></div>"""))

        elif path == "/login":
            self.send(page(s, """<div class=card><h2>Area Clienti</h2>
<form method=post action=/login>
<input name=u placeholder="Username">
<input name=p type=password placeholder="Password">
<button>Accedi</button></form>
<p class=warn>Accesso riservato ai correntisti.</p></div>"""))

        elif path == "/logout":
            self.send(page(None, "<div class=card>Disconnesso. "
                                 "<a href=/>Home</a></div>"),
                      cookie="session=; Max-Age=0; Path=/")

        elif path == "/dashboard":
            if not s:
                return self._redir("/login")
            self.send(page(s, f"""<div class=card><h2>Ciao {s['u']}</h2>
<p>Saldo disponibile: <b>&euro; 12.480,33</b></p>
<p>IBAN: IT60 X054 2811 1010 0000 0123 456</p>
<p>Accesso riuscito. Badge di sicurezza:
<span class=flag>FLAG{{sql1_4uth_byp4ss}}</span></p></div>"""))

        elif path == "/account":
            if not s:
                return self._redir("/login")
            uid = f(get, "id", "")
            if not uid:
                row = q(f"SELECT * FROM users WHERE username='{s['u']}'")
            else:
                row = q(f"SELECT * FROM users WHERE id={uid}")
            if not row:
                return self.send(page(s, "<div class=card>Utente "
                                         "non trovato.</div>"))
            r = row[0]
            self.send(page(s, f"""<div class=card><h2>Profilo #{r[0]}</h2>
<table><tr><th>Username</th><td>{r[1]}</td></tr>
<tr><th>Nome</th><td>{r[4]}</td></tr>
<tr><th>Ruolo</th><td>{r[3]}</td></tr>
<tr><th>Nota privata</th><td>{r[5]}</td></tr></table>
<p class=warn>Puoi vedere solo il tuo profilo.</p></div>"""))

        elif path == "/search":
            if not s:
                return self._redir("/login")
            query = f(get, "q", "")
            rows, err = [], ""
            if query:
                sql = ("SELECT description, amount FROM transactions "
                       f"WHERE description LIKE '%{query}%'")
                try:
                    rows = q(sql)
                except Exception as e:
                    err = f"<p class=warn>Errore DB: {e}</p>"
            trs = "".join(f"<tr><td>{r[0]}</td><td>{r[1]}</td></tr>"
                          for r in rows)
            self.send(page(s, f"""<div class=card><h2>Cerca movimenti</h2>
<form><input name=q value="{query}" placeholder="Cerca descrizione...">
<button>Cerca</button></form>{err}
<table><tr><th>Descrizione</th><th>Importo</th></tr>{trs}</table></div>"""))

        elif path == "/guestbook":
            rows = q("SELECT author, message FROM guestbook")
            items = "".join(f"<p><b>{a}</b>: {m}</p>" for a, m in rows)
            self.send(page(s, f"""<div class=card><h2>Guestbook</h2>{items}
<form method=post action=/guestbook>
<input name=author placeholder="Nome">
<textarea name=message placeholder="Messaggio"></textarea>
<button>Invia</button></form></div>"""))

        elif path == "/download":
            if not s:
                return self._redir("/login")
            name = f(get, "file", "estratto_conto.pdf")
            name = name.replace("../", "")  # path traversal "fix"
            fp = os.path.join(BASE, "files", name)
            try:
                with open(fp, "rb") as fh:
                    data = fh.read()
                self.send(data, 200, "application/octet-stream")
            except Exception:
                self.send(page(s, "<div class=card>File non trovato.</div>"),
                          404)

        elif path == "/admin":
            if not s or s.get("role") != "admin":
                return self.send(page(s, "<div class=card><h2>403</h2>"
                                         "Accesso negato. Solo admin.</div>"),
                                 403)
            self.send(page(s, """<div class=card><h2>Pannello Admin</h2>
<p>Benvenuto amministratore. Badge:
<span class=flag>FLAG{c00k13_f0rg3ry_4dm1n}</span></p>
<h3>Diagnostica di rete</h3>
<form method=post action=/admin/ping>
<input name=host value="127.0.0.1" placeholder="host da pingare">
<button>Ping</button></form></div>"""))

        elif path == "/robots.txt":
            self.send("""User-agent: *
Disallow: /backup
Disallow: /admin
Disallow: /internal
""", 200, "text/plain")

        elif path == "/backup":
            self.send(page(s, """<div class=card><h2>/backup</h2>
<ul><li><a href=/backup/config.bak>config.bak</a></li>
<li><a href=/backup/db_dump.sql>db_dump.sql</a></li></ul>
<p class=warn>Directory dimenticata dal deploy del 2023. TODO: rimuovere.</p>
</div>"""))

        elif path in ("/backup/config.bak", "/backup/db_dump.sql"):
            fname = os.path.basename(path)
            with open(os.path.join(BASE, "backup", fname), "rb") as fh:
                self.send(fh.read(), 200, "text/plain; charset=utf-8")

        else:
            self.send(page(s, "<div class=card><h2>404</h2>Pagina "
                              "inesistente.</div>"), 404)

    def do_POST(self):
        path, get, post, f = self.params()

        if path == "/login":
            u, p = f(post, "u"), f(post, "p")
            # VULN: classic SQL injection on login
            sql = (f"SELECT * FROM users WHERE username='{u}' "
                   f"AND password='{hashlib.md5(p.encode()).hexdigest()}'")
            try:
                rows = q(sql)
            except Exception as e:
                s = self.sess()
                return self.send(page(s, f"<div class=card>Errore DB: {e}"
                                         "</div>"), 500)
            if rows:
                r = rows[0]
                tok = make_session(r[1], r[3])
                self.send_response(302)
                self.send_header("Location", "/dashboard")
                self.send_header("Set-Cookie", f"session={tok}; Path=/")
                self.end_headers()
                return
            s = self.sess()
            self.send(page(s, "<div class=card>Credenziali non valide. "
                              "<a href=/login>Riprova</a></div>"), 401)

        elif path == "/guestbook":
            con = sqlite3.connect(DB)
            con.execute("INSERT INTO guestbook(author,message) VALUES(?,?)",
                        (f(post, "author"), f(post, "message")))
            con.commit()
            con.close()
            self._redir("/guestbook")

        elif path == "/admin/ping":
            s = self.sess()
            if not s or s.get("role") != "admin":
                return self.send("Forbidden", 403)
            host = f(post, "host", "127.0.0.1")
            # VULN: command injection
            try:
                out = subprocess.check_output(
                    f"ping -n 1 {host}", shell=True,
                    stderr=subprocess.STDOUT, timeout=10)
                res = out.decode("cp850", "replace")
            except Exception as e:
                res = str(e)
            self.send(page(s, f"<div class=card><h2>Diagnostica</h2>"
                              f"<pre>{res}</pre>"
                              "<a href=/admin>Indietro</a></div>"))

        else:
            self.send("Not found", 404)

    def _redir(self, loc):
        self.send_response(302)
        self.send_header("Location", loc)
        self.end_headers()


if __name__ == "__main__":
    if "--reset" in sys.argv and os.path.exists(DB):
        os.remove(DB)
    init_db()
    print(f"[*] VaultCore Bank on http://0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
