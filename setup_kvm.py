'''
Created on: 17th May
@Author: Priyanka G. Dodia (pgdodia@hbku.edu.qa)

SERVER (Host) environment setup: PART 1
----------------------------------------

KVM (nested virtualization required to run emulator on server)
---------------------------------------------------------------
egrep -c '(vmx|svm)' /proc/cpuinfo > 0
uname -m => x86_64
sudo apt update
sudo apt-get install qemu-kvm libvirt-bin ubuntu-vm-builder bridge-utils OR
sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
sudo adduser `id -un` libvirt
sudo adduser `id -un` kvm
RE-LOGIN
virsh list --all
'''

import os, sys

def kvm_setup():
	print("egrep -c '(vmx|svm)' /proc/cpuinfo")
	op = os.popen("egrep -c '(vmx|svm)' /proc/cpuinfo").read().rstrip()
	if int(op) == 0:
		print(op)
		print("Value must be > 0.\nServer not compatible to run emulator! Exiting setup.")
		return
	print(op, ": Requirement Satisfied!")
	print("uname -m")

	op = os.popen("uname -m").read().rstrip()
	if not "x86_64" in op:
		print(op)
		print("Need x86_64 arch server.\nServer not compatible to run the emulator! Exiting setup.")
		return
	print(op, ": Requirement Satisfied!")

	print("sudo apt update")
	os.system("sudo apt update")

	#print("sudo apt-get install qemu-kvm libvirt-bin ubuntu-vm-builder bridge-utils")
	#os.system("sudo apt-get install qemu-kvm libvirt-bin ubuntu-vm-builder bridge-utils").read()

	print("sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils")
	os.system("sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils")

	print("sudo adduser `id -un` libvirt")
	os.system("sudo adduser `id -un` libvirt")

	print("sudo adduser `id -un` kvm")
	os.system("sudo adduser `id -un` kvm")

	print("KVM/QEMU (nested virtualization) pre-req setup COMPLETED SUCCESSFULLY!\nTODO: Re-login now! (required for changes to take effect, before installing DOCKER)")
	return


kvm_setup()
