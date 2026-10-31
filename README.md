# VaultCore Bank — Vulnerable Web Lab

Lab CTF locale: una web app **volutamente vulnerabile** (finta banca online)
con 7 flag `FLAG{...}` da catturare. Solo Python stdlib, zero dipendenze.

> ⚠️ NON esporre su internet o reti pubbliche. È volutamente insicura,
> serve solo come target di esercitazione in locale.

## Avvio del target

```powershell
# Windows (PowerShell)
.\start.ps1        # oppure: python app.py
```

Ascolta su `0.0.0.0:1337`. Da WSL2 si raggiunge all'IP dell'host
(`ip route show default` dentro WSL), es. `http://172.24.64.1:1337`.

Reset database: `python app.py --reset`

## Exploit

```bash
pip install requests   # se serve
python3 exploit.py http://172.24.64.1:1337
```

Esegue l'intera catena e stampa le 7 flag:

| # | Vulnerabilità | Dove |
|---|---------------|------|
| 1 | SQLi auth bypass | `POST /login` |
| 2 | IDOR | `GET /account?id=N` |
| 3 | UNION-based SQLi | `GET /search?q=` |
| 4 | Info disclosure | `robots.txt` → `/backup` |
| 5 | Forging cookie firmato (HMAC-SHA256, chiave trapelata) | `GET /admin` |
| 6 | OS command injection | `POST /admin/ping` |
| 7 | LFI / path traversal (filtro bypassabile con `....//`) | `GET /download?file=` |

Bonus: stored XSS nel guestbook (`POST /guestbook`).

## Struttura

```
app.py      # il target vulnerabile
exploit.py  # exploit automatico, cattura tutte le flag
backup/     # file "dimenticati" (flag 4 + jwt_secret)
internal/   # raggiungibile solo via LFI
secret/     # flag finale, via command injection
files/      # file serviti da /download
```
