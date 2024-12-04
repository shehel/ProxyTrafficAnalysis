1. Install Virtualization Tools
sudo apt install qemu-system qemu-kvm
2. Install the Android Emulator
sudo apt install google-android-emulator-installer

3.Configure Environment Variables
export ANDROID_SDK_ROOT=/pathto/androidsdk
export ANDROID_AVD_HOME=/pathto/.android/avd
export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_SDK_ROOT/platform-tools
export PATH=$PATH:$ANDROID_SDK_ROOT/tools
export PATH=$PATH:$ANDROID_SDK_ROOT/emulator
export PATH=$PATH:$ANDROID_SDK_ROOT/tools/bin
4. verify installation
emulator -version
adb --version
5. Launch emulator for test 
emulator -avd avd30


