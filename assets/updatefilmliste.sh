#!/bin/bash

script_path=$(dirname $(realpath -s $0))

curl -sk $(curl -sk https://res.mediathekview.de/akt.xml | grep --only-matching --perl-regexp "https[^<]+") | # get the raw file
unxz | # uncompress it
grep --perl-regex --only-matching '(?<=,"Filmliste":).+' | # remove meta information in the beginning (don't use sed because this seems to have some line length limit)
sed 's/}$//' | # remove the } in the end
sed 's/,"X":/\n/g' | # split by record, remove the JSON key (X), and keep only the JSON value(s)
cat > "${script_path}/filmliste.txt"

