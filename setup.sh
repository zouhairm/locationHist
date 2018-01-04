#!/bin/sh

git submodule update --init
cd countries
touch __init__.py
wget http://thematicmapping.org/downloads/TM_WORLD_BORDERS-0.3.zip
unzip TM_WORLD_BORDERS-0.3.zip
cd ..

