#/usr/bin/env bash
ZIP_URL=$(lynx -nonumbers -dump -listonly http://reta-vortaro.de/tgz/ | grep revoxml)
VERSION=$(echo $ZIP_URL | tr -dc '0-9')
wget -O revoxml.zip $ZIP_URL
rm -rf revo/cfg revo/dtd revo/smb revo/stl revo/xml revo/xsl
unzip revoxml.zip
echo $VERSION > revo/VERSION