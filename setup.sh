#!/bin/sh
python3 -c 'import os; assert "VIRTUAL_ENV" in os.environ, "Please run in a virtual env"'

pip3 install GDAL==$(gdal-config --version | awk -F'[.]' '{print $1"."$2}')
pip3 install -r requirements.txt
