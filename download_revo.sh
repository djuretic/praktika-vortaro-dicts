#/usr/bin/env bash
wget -O revoxml.zip $(lynx -nonumbers -dump -listonly http://reta-vortaro.de/tgz/ | grep revoxml) && unzip revoxml.zip
