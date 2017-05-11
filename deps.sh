#!/bin/bash -xe

apt-get install -y dpkg-dev
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install coin
