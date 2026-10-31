#!/bin/bash
mkdir -p ~/hacklab
cp -r /mnt/c/Users/Nicola/CascadeProjects/2048/hacklab/. ~/hacklab/
rm -rf ~/hacklab/data ~/hacklab/__pycache__
cd ~/hacklab && git init -q && git add -A && git -c user.name=brawlnic -c user.email=brawlnic@users.noreply.github.com commit -qm "VaultCore Bank vuln lab + exploit + vcforge tool" && git log --oneline && echo "---" && find ~/hacklab -type f -not -path "*/.git/*" | sort
