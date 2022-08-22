#!/bin/bash

script_path=$(dirname $(realpath -s $0))

(
  cd ${script_path}
  assets/updatefilmliste.sh
  rm -rf cache/temp
  python src/main.py
)

