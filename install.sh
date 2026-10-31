#!/bin/sh
# vcforge one-liner installer — adds brawlnic's apt repo and installs vcf.
#   curl -fsSL https://brawlnic.github.io/hacklab/install.sh | sudo bash
set -e

REPO_URL="https://brawlnic.github.io/hacklab/apt"
KEYRING=/usr/share/keyrings/brawlnic.gpg
LIST=/etc/apt/sources.list.d/brawlnic.list

command -v curl >/dev/null 2>&1 || { apt-get update && apt-get install -y curl; }
command -v gpg  >/dev/null 2>&1 || { apt-get update && apt-get install -y gpg; }

echo "[*] downloading repo key..."
curl -fsSL "$REPO_URL/brawlnic.asc" | gpg --dearmor -o "$KEYRING"

echo "[*] adding repo brawlnic..."
echo "deb [signed-by=$KEYRING] $REPO_URL stable main" > "$LIST"

echo "[*] installing vcf..."
apt-get update -qq
apt-get install -y vcf

echo "[+] done. try:  vcf --help"
