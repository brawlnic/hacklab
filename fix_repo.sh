#!/bin/bash
cd ~/hacklab
rm -f copy_wsl.sh
rm -rf vcforge/build vcforge/vcforge.egg-info
git rm -q --cached copy_wsl.sh vcforge/build vcforge/vcforge.egg-info 2>/dev/null
git add -A
git -c user.name=brawlnic -c user.email=brawlnic@users.noreply.github.com commit -qm "cleanup: remove build artifacts" 2>/dev/null
echo "=== file tracciati nel repo ==="
git ls-files
