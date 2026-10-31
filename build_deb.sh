#!/bin/bash
set -e
SRC=/mnt/c/Users/Nicola/CascadeProjects/2048/hacklab/vcforge
PKG=/tmp/vcf_0.3.1_all
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" "$PKG/usr/lib/python3/dist-packages/vcforge" "$PKG/usr/bin"
cp "$SRC/deb/control" "$PKG/DEBIAN/control"
cp "$SRC"/vcforge/*.py "$PKG/usr/lib/python3/dist-packages/vcforge/"
cat > "$PKG/usr/bin/vcf" <<'EOF'
#!/bin/sh
exec python3 -m vcforge "$@"
EOF
chmod 755 "$PKG/usr/bin/vcf"
cp "$PKG/usr/bin/vcf" "$PKG/usr/bin/vcforge"
dpkg-deb --build "$PKG" /home/nicola/hacklab/vcf_0.3.1_all.deb
echo "=== built ==="
dpkg-deb -I /home/nicola/hacklab/vcf_0.3.1_all.deb | head -14
