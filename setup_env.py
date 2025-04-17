'''
Server environment setup script (Note: To be run before running experiment 'run_experiment.py'
@Author: Priyanka G. Dodia (pgdodia@hbku.edu.qa)
Qatar Computing Research Institute
'''

import os,sys
import setup_kvm as skvm
import setup_zeek as szeek

global ANDROID_HOME
ANDROID_HOME = "/opt/androidsdk"


def start_libvirt():
	os.system("sudo apt-get update")
	os.system("sudo apt-get install -y qemu qemu-kvm libvirt-bin  bridge-utils  virt-manager")
	os.system("sudo service libvirtd start")
	os.system("service libvirtd status")
	return

# Setup env and install Android SDK, tools and system image(s)
# android version(av) = 30 will be installed
def setup_env():
	curdr = os.getcwd()
	skvm.kvm_setup()
	print("Starting 'libvirtd' required for nested virtualization...")
	start_libvirt()
	print("Ensure root access")
	os.system("sudo su")
	print("Installing Android SDK")
	os.system("bash "+curdr+"/install_sdk.sh")
	print("Installed system image: android-30")
	os.chdir(ANDROID_HOME+"/system-images")
	print("Images downloaded at PATH: ",ANDROID_HOME+"/system-images")
	os.system("ls")
	print("Re-login/Re-start server for KVM changes to take effect.")
	return

setup_env()
#szeek.zeek_install() # Uncomment if you wish to install zeek on the server
