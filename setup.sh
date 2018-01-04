#!/bin/sh

git submodule update --init
cd countries
git apply ../countries.patch
wget http://thematicmapping.org/downloads/TM_WORLD_BORDERS-0.3.zip
unzip TM_WORLD_BORDERS-0.3.zip
cd ..

