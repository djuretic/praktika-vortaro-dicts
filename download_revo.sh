#/usr/bin/env bash
set -o errexit
set -o nounset
ZIP_URL=$(lynx -nonumbers -dump -listonly https://github.com/revuloj/revo-fonto/releases | grep "tags/" | grep "zip" | head -n1)
wget -O revoxml.zip $ZIP_URL
# this will include trailing slash
ZIP_ROOT_DIR=$(unzip -l revoxml.zip | sed -n "5p" | awk -F" " '{print $4}')
rm -rf revo/xml
unzip -jo revoxml.zip "${ZIP_ROOT_DIR}revo/*" -d "revo/xml/"

wget -O revo/dtd/vokomll.dtd https://raw.githubusercontent.com/revuloj/voko-grundo/master/dtd/vokomll.dtd
wget -O revo/dtd/vokourl.dtd https://raw.githubusercontent.com/revuloj/voko-grundo/master/dtd/vokourl.dtd
wget -O revo/dtd/vokosgn.dtd https://raw.githubusercontent.com/revuloj/voko-grundo/master/dtd/vokosgn.dtd
wget -O revo/cfg/lingvoj.xml https://raw.githubusercontent.com/revuloj/voko-grundo/master/cfg/lingvoj.xml
wget -O revo/cfg/fakoj.xml https://raw.githubusercontent.com/revuloj/voko-grundo/master/cfg/fakoj.xml
