'''
Control script to INSTALL & EXECUTE APK in headless emulator
Created on: 17th May 2023
Modified on: 29th May 2023
@Author: Priyanka G. Dodia (pgdodia@hbku.edu.qa)
Qatar Computing Research Institute
'''

import os
import time

# Note: apkpath => curdr+/apkfiles/apkname.apk
def install_apk(apkpath):
	print("Ensure emulator is available for APK installation....")
	result = os.popen("adb devices").read()
	if "emulator-5554" and "offline" in result:
		print("Emulator status: OFFLINE. Sleeping for 2mts before RETRY")
		time.sleep(120) # sleep 2mts for emulator to come up

	print("Attempting APK INSTALLATION......")
	print("adb -s emulator-5554 install -g "+apkpath)
	status = os.popen("adb -s emulator-5554 install -g "+apkpath).read()
	if "Success" in status:
		return True

	return False

def execute_apk(package, mainactivity):
	print("Executing installed APK with package name: ",package)

	if mainactivity == None or mainactivity == 'None':
		print("adb shell -s emulator-5554 shell monkey -p "+package+" -c android.intent.category.LAUNCHER 1")
		result = os.popen("adb shell -s emulator-5554 shell monkey -p "+package+" -c android.intent.category.LAUNCHER 1").read()
	else:
		print("CMD1: adb shell am start -n 'package/mainactivity'")
		result = os.popen("adb shell am start -n '"+package+"/"+mainactivity+"'").read()

	if "Error" in result:
		print("Failed APK Installation!\nAttempting execution of APK again....")
		print("adb shell -s emulator-5554 shell monkey -p "+package+" -c android.intent.category.LAUNCHER 1")
		rerun = os.popen("adb shell -s emulator-5554 shell monkey -p "+package+" -c android.intent.category.LAUNCHER 1").read()
		print("Result of 2nd attempt at APK execution: \n",rerun)
	else:
		print("Execution Successful! APK is running on the emulator......")
	return


def main(apkpath, package, mainactivity):
	if not os.path.isfile(apkpath):
		print("APK not in 'apkfiles/' at current working directory. Pls check apk file is at path!")
		return False

	if package == None or package == "None":
		print("Couldn't locate package name for APK. Skipping......")
		return False

	success = install_apk(apkpath)
	if success:
		execute_apk(package, mainactivity)
		return True
	else:
		print("Initial APK installation attempt failed. RETRYING....")
		time.sleep(10)
		print("Retrying APK installation.....")
		success = install_apk(apkpath)
		if success:
			execute_apk(package, mainactivity)
			return True
		else:
			print("Attempts at APK installations failed! Pls check emulator is running?")
			return False

