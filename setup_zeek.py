'''
Setup script to install Zeek on Ubuntu servers (independent optional script)
@Author: Priyanka G. Dodia (pgdodia@hbku.edu.qa)
Qatar Computing Research Institute
'''


'''
To upgrade cmake:
==================
DOWNLOAD:
https://cmake.org/download/ : Download .sh of latest cmake version
INSTALL:
sudo mkdir /opt/cmake
sudo sh <installer filename> --prefix=/opt/cmake
sudo ln -s /opt/cmake/bin/cmake /usr/local/bin/cmake
'''

import os, sys

def zeek_install():
	os.system("sudo apt-get install cmake make gcc g++ flex bison libpcap-dev libssl-dev python3 python3-dev python3-git python3-semantic-version swig zlib1g-dev libjemalloc-dev")
	os.system("sudo apt-get update")
	os.system("sudo apt-get dist-upgrade")
	print("Creating user zeek (Enter passwd: zeek)")
	os.system("sudo groupadd zeek")
	os.system("sudo adduser zeek")
	os.system("sudo usermod -aG zeek zeek")
	os.system("sudo mkdir /opt/zeek")
	os.system("sudo chown -R zeek:zeek /opt/zeek")
	os.system("sudo chmod 750 /opt/zeek")
	os.system("su zeek")
	os.chdir("/home/zeek")
	os.system("wget https://download.zeek.org/zeek-5.2.1.tar.gz")
	os.system("tar -xzvf zeek-5.2.1.tar.gz")
	os.chdir("/home/zeek/zeek-5.2.1")
	os.system("./configure --prefix=/opt/zeek --enable-jemalloc --build-type=release")
	print("This may take longer than 5 minutes...")
	os.system("make")
	os.system("make install")
	os.system('touch ~/.bashrc | export PATH="/opt/zeek/bin:$PATH"')
	os.system("source ~/.bashrc")
	os.system("exit")
	return

# Zeek will be in : /opt/zeek/bin/zeek
zeek_install()
