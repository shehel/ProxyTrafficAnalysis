#!/bin/bash -i
# Takes $1=> pcapname as argument
#using shebang with -i to enable interactive mode (auto load .bashrc)
#this script was inspired from https://docs.travis-ci.com/user/languages/android/

set -e #stop immediately if any error happens

pcap_name=$1
avd_name=$2

if [[ -z "$avd_name" ]]; then
  avd_name="avd30"
fi

#check if emulator work well
emulator -version

# create virtual device, default using Android 9 Pie image (API Level 28)
echo no | /home/mrabhi/androidsdk/tools/bin/avdmanager create avd --force  -n avd30 -k "system-images;android-30;google_apis;x86_64"

# start the emulator
emulator -avd avd30 -no-audio -no-window -wipe-data -tcpdump $1 &

# show connected virtual device
adb devices
