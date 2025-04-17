import os, sys
import controlapk as runapk
import interactapk as iapk
import time
from datetime import datetime
import subprocess
import subprocess
import timeout_decorator
from timeout_decorator.timeout_decorator import TimeoutError
import xml.dom.minidom as xx
import random
import re

global ANDROID_HOME
global EMU_PATH
global PCAP_PATH
global curdr

# Updated paths based on the new setup
# Set environment variables or use defaults
ANDROID_HOME = os.getenv('ANDROID_HOME')
ROOTAVD_PATH = os.getenv('ROOTAVD_PATH')
EMU_PATH = os.getenv('EMU_PATH')
PCAP_PATH = os.getenv("PCAP_PATH", "/default/pcap/path")
SCRIPT_DIR = os.getenv("SCRIPT_DIR", "/default/script/path")

# Change to the scripts directory
import os
os.chdir(SCRIPT_DIR)

# Print current working directory
curdr = os.getcwd()
print("Current working directory:", curdr)

# Define the path for search keywords
SEARCH_KWDS = curdr + "/res/search_key_words_october"
print("Search keywords path:", SEARCH_KWDS)

# Global variable example
global clickkwds

clickkwds = ["同意","accept all", "accept & continue", "no thanks", "start", "enter", "i agree", "ok", "skip", "allow", "continue", "agree", "got it", "got it!", "yes", "continue in browser", "i got it", "always", "agree & continue", "retry", "only this time", "yes i am 18+", "accept all cookies", "accept cookies", "not now", "maybe later", "yes, i am happy", "i accept", "accept all", "allow all cookies", "allow all", "accept cookies & continue", "cancel", "accept & close", "i am 18 or older", "applica", "accetta e continua", "near me", "jai compris", "jeg forstår", "accetta", "accetta tutti", "chiudi video", "chiudi", "__ 滿 18 歲, 請按此 __"]
global loginkwds
loginkwds = ["log in", "login", "sign in", "sign in with email", "already a member? log in", "账号密码登录"]
global acckwds
acckwds = ["continue as testhy", "fm_login_id", "username", "email", "phone number", "account no", "account number", "email_input_container", "session_key", "账号", "手机号", "邮箱"]
global nonclickables
nonclickables = ["com.android.chrome:id/home_button", "com.android.chrome:id/location_bar", "com.android.chrome:id/location_bar_status", "com.android.chrome:id/location_bar_status_icon", "com.android.chrome:id/url_bar", "com.android.chrome:id/toolbar_buttons", "com.android.chrome:id/tab_switcher_button", "com.android.chrome:id/menu_button_wrapper","com.android.chrome:id/menu_button", "com.android.chrome:id/toolbar_shadow", "com.android.chrome:id/translate_infobar_menu_button", "com.android.chrome:id/infobar_close_button"]

search_kwds = []
with open(SEARCH_KWDS, 'r') as f:
    for line in f.readlines():
        kwd = line.rstrip()[:-1]
        search_kwds.append(kwd)
    print(len(search_kwds))

global searchkwds
searchkwds = search_kwds

global search_bar_kwds
search_bar_kwds = ["search input", "google search", "submit", "search-box", "searchbox_input", "keyword"]

#Available and useful view size [0, 280] [1440, 2392]
def get_domains(basep):
    domains = []
    with open(basep, 'r') as f:
        for line in f.readlines():
            domain_info = line.rstrip().split(" ")
            domains += [domain_info] #['https://'+domain+'/']
    return domains[1:]

def stop_emu(pid=None):
    #x = os.popen('tasklist | findstr "qemu-system-x86_64.exe').read()
    emu_path = EMU_PATH
    x = os.popen('ps aux | grep "emulator"').read()
    print("Running processes: ", x)
    if emu_path not in x:
        print("No running emulator to stop!")
        return
    xx = x.split("\n")
    for proc in xx:
        if emu_path in proc:
            print("TO KILL:", proc)
            pid = proc.split('  ')[1].strip().split(" ")[0].rstrip()
            print("Killing PID: ",pid)
            os.system("kill -9 "+pid)
            os.system("pkill -f emulator")
            print("Sleeping for clean emulator shutdown.....")
            time.sleep(30)
            break

    return

def get_app_uid(package_name):
    """
    Retrieve the UID of an app by its package name and convert from u0_aXXX format to numeric UID.
    Android apps with UID format u0_aXXX have a numerical UID of 10000 + XXX.

    Args:
        package_name (str): The package name of the Android app

    Returns:
        str: Numeric UID if found and converted successfully, None otherwise
    """
    try:
        result = os.popen(f"adb shell dumpsys package {package_name} | grep userId").read()
        if "userId=" in result:
            uid_part = result.split("userId=")[1].strip()

            # Handle u0_aXXX format
            if uid_part.startswith("u0_a"):
                # Extract the number after u0_a
                app_id = uid_part.split("u0_a")[1]
                # Strip any non-numeric characters
                app_id = ''.join(filter(str.isdigit, app_id))

                if app_id.isdigit():
                    # Convert to numeric UID (10000 + app number)
                    numeric_uid = str(10000 + int(app_id))
                    return numeric_uid

            print(f"Could not convert UID format for {package_name}: {uid_part}")
            return None
        else:
            print(f"Unable to find UID for package: {package_name}")
            return None

    except Exception as e:
        print(f"Error while retrieving UID for {package_name}: {e}")
        return None

def start_emu(pcapname, av='30', wipe_data=True):

    if not os.path.isfile(EMU_PATH+"/emulator"):
        print("Emulator bash script missing!")

    print("Starting emulator with android-"+av)
    os.chdir(EMU_PATH)

    if wipe_data:
        pid = subprocess.Popen("./emulator -avd pixel_30 -no-audio -wipe-data",shell=True,preexec_fn=os.setsid,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    else:
        pid = subprocess.Popen("./emulator -avd pixel_30 -no-audio",shell=True,preexec_fn=os.setsid,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    #pid = subprocess.Popen("./emulator -avd pixel_30 -no-audio -wipe-data -tcpdump " + pcapname, shell=True,preexec_fn=os.setsid,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    #pid = subprocess.Popen("./emulator -avd pixel_30 -no-audio -no-window -wipe-data ", shell=True,preexec_fn=os.setsid,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print("Started emulator with PID: ",pid)
    os.system('ps aux | grep "emulator"')
    #os.system('tasklist| findstr "emulator"')
    print("Sleeping 60 seconds for clean emulator startup....")
    os.chdir(curdr)
    if av == "31":
        time.sleep(60)
    else:
        time.sleep(60)

    print("Running adb as root....")
    os.system("adb root")
    return

def check_status():
    print("Ensure emulator is available for open GOOGLE CHROME....")
    result = os.popen("adb devices").read()
    if "emulator-5554" and "offline" in result:
        print("Emulator status: OFFLINE. Sleeping for 2mts before RETRY")
        time.sleep(120) # sleep 2mts for emulator to come up
        result = os.popen("adb devices").read()
        if "emulator-5554" and "offline" in result:
            return False
        else:
            return True
    else:
        return True

def open_chrome(package='com.android.chrome', mainactivity="com.google.android.apps.chrome.Main"):

    #mainactivity = 'com.google.android.apps.chrome.IntentDispatcher'
    status = check_status()
    if not status:
        print("Emulator status: OFFLINE. Cannot open GOOGLE CHROME.")
        return status, False

    #adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main
    print("Executing installed GOOGLE CHROME with package name: ",package)
    print("CMD1: adb shell am start -n 'package/mainactivity'")
    result = os.popen("adb shell am start -n "+package+"/"+mainactivity).read()

    if "Error" in result:
        print("Failed execution of GOOGLE CHROME....")
        rerun = os.popen("adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main").read()
        print("Result of 2nd attempt at APK execution: \n",rerun)
        if "Error" in result:
            return status, False
        else:
            return status, True
    else:
        print("Execution Successful! GOOGLE CHROME is running on the emulator......")
        return status, True

def get_uidump():
    os.system("rm window_dump.xml")
    print("1* Getting App UI dump file.....")
    curdr = os.getcwd()
    result = os.popen('adb shell uiautomator dump').read()
    if "ERROR" in result or "error" in result or "Error" in result:
        return False
    result = os.popen('adb pull sdcard/window_dump.xml '+curdr+'/.').read()
    if "ERROR" in result or "error" in result or "Error" in result:
        return False
    dumpf = curdr+"/window_dump.xml"
    print("Finish dumping UI......")
    return dumpf

def execute_click(x, y):
    print("adb shell input tap "+x+" "+y)
    os.system("adb shell input tap "+x+" "+y)
    return

def execute_click_middle(x, y, xxe, yye):
    print("Click at the middle position......")
    point_x = str(int((int(x)+int(xxe))/2))
    point_y = str(int((int(y)+int(yye))/2))
    print("adb shell input mouse -d 0 tap "+point_x+" "+point_y)
    os.system("adb shell input tap "+point_x+" "+point_y)
    return

# Earnitapp: adb shell input swipe 475 1086 965 1282 300
def execute_scroll(x, y, xxe, yye, duration="3000"):
    nulllst = ["None", None]
    if not (x in nulllst and y in nulllst and xxe in nulllst and yye in nulllst):
        print("adb shell input swipe "+x+" "+y+" "+xxe+" "+yye+" "+duration)
        os.system("adb shell input swipe "+x+" "+y+" "+xxe+" "+yye+" "+duration)
    return

def execute_enter():
    os.system("adb shell input keyevent 66")
    return

def execute_tab():
    os.system("adb shell input keyevent 61")
    return

def enter_text(text):
    os.system("adb shell input text '"+text+"'")
    return

def execute_back():
    os.system("adb shell input keyevent 4")
    return

def execute_page_down():
    os.system("adb shell input keyevent 93")

def execute_page_up():
    os.system("adb shell input keyevent 92")

def is_login_kwd(k):
    word = k.lower()
    for keywd in loginkwds:
        #print(word, "in", keywd, "?")
        if word == keywd:
            return True
    return False

def is_account_kwd(k):
    word = k.lower()
    for keywd in acckwds:
        if word == keywd or keywd in word:
            return True
    return False

def get_coordinates(coordinates):
    cc = coordinates.strip("[").strip("]").split("][")
    x = cc[0].split(",")[0]  # x_start
    y = cc[0].split(",")[1]  # y_start
    xxe = cc[1].split(",")[0] # x_end
    yye = cc[1].split(",")[1] # y_end

    return (x, y, xxe, yye)

def get_url(dumpf):
    url = ''
    print("Start getting url......")
    if not os.path.isfile(dumpf):
        print("Failed to obtaine UI dump for APK. Exiting UI interaction")
        return False
    else:
        print("Dump file exists. Start processing next steps.")

    dump = xx.parse(dumpf)
    if dump == None:
        return False

    nodes = dump.getElementsByTagName("node")
    for elem in nodes:
        uitype = elem.getAttribute("resource-id") #switch_btn
        if uitype == "com.android.chrome:id/url_bar":
            url = elem.getAttribute("text")
            break
    print(url)
    return url

def get_actions(dumpf):
    actiondt = dict()
    #url = ''
    print("Start getting actions......")
    if dumpf == False:
        return False

    if not os.path.isfile(dumpf):
        print("Failed to obtaine UI dump for APK. Exiting UI interaction")
        return False
    else:
        print("Dump file exists. Start processing next steps.")

    dump = xx.parse(dumpf)
    if dump == None:
        return False

    nodes = dump.getElementsByTagName("node")
    print(len(nodes))
    for elem in nodes:
        actionname = elem.getAttribute("text")
        if len(actionname) == 0:
            actionname = elem.getAttribute("content-desc")
            if len(actionname) == 0:
                actionname = elem.getAttribute("resource-id")
        uitype = elem.getAttribute("resource-id") #switch_btn
        #if uitype == "com.android.chrome:id/url_bar":
        #	url = actionname
        if uitype in nonclickables:
            continue
        checkable = elem.getAttribute("checkable")
        clickable = elem.getAttribute("clickable")
        scrollable = elem.getAttribute("scrollable")
        longclickable = elem.getAttribute("long-clickable")
        coordinates = elem.getAttribute("bounds")
        coordinates = get_coordinates(coordinates)
        if int(coordinates[1]) <= 280:
            continue
        #print(coordinates)
        enabled = elem.getAttribute("enabled")
        focusable = elem.getAttribute("focusable")
        ##print("NODE: ",actionname, "checkable: ", checkable," clickable: ",clickable," scrollable: ",scrollable," longclickable: ", longclickable)
        if len(actionname) >= 1 and not actionname in actiondt:
            if (checkable == "true" or clickable == "true" or scrollable == "true" or longclickable == "true") and enabled == "true":
            ##print("Adding: ",actionname," to action list")
                actiondt[actionname] = {"xy": coordinates, "uitype": uitype, "checkable": checkable, "clickable": clickable, "scrollable": scrollable, "longclickable": longclickable, "enabled": enabled, "focusable": focusable}
                #print("NODE: ",actionname, "checkable: ", checkable," clickable: ",clickable," scrollable: ",scrollable," longclickable: ", longclickable)

    print("Finish getting", len(actiondt), "actions......")
    return actiondt

def sort_actions(actiondt):
    ##print(actiondt)
    # click/checkwords: [xx,yy,xx_end,yy_end]
    clickables = dict()
    #check = dict()
    # clickable & enabled
    for k, v in actiondt.items():
        clickable = v["clickable"]
        enabled = v["enabled"]
        #checkable = v["checkable"]
        xx, yy, xxe, yye = v['xy']
        buttontype = v["uitype"]
        if clickable and enabled:
            clickables[k] = [xx,yy,xxe,yye,buttontype]

    return clickables

def choose_action(clickables):
    click_order = []

    for k, v in clickables.items():
        #print("Clickable key: ", k)
        if is_in_kwds(k): # or "button_next" in v[-1]:
            print("Has click keywords")
            print("(",v,",",k,")")
            click_order += [(v, k)]

    #click_order.sort(key=lambda x: (x[0][0],x[1][1]))
    print("Click order: ", click_order)
    return click_order

def perform_click(x, y, xxe, yye, acttype):
    nulllst = ["None", None]
    print("Performing click.......")
    if "switch_btn" in acttype or "swipe_to_login" in acttype: #or "permissioncontroller" in acttype:
        print("Swiping switch button")
        execute_scroll(x, y, xxe, yye)
        return True
    else:
        #if not (x in nulllst and y in nulllst):
        if not (x in nulllst and y in nulllst and xxe in nulllst and yye in nulllst):
            print("Tapping (x,y): ",x,y)
            execute_click_middle(x, y, xxe, yye)
            return True
        else:
            print("Clicking ENTER (coordinates not found)")
            execute_enter() # plain enter if failed to obtain x,y coordinates
            return False

def perform_scroll():
    print("Start scroll the web page......")
    idx = random.randint(0, 5)
    lcd_height = 640
    lcd_width = 320
    if idx == 0:
        print("1/3 page will be scrolled down")
        execute_scroll('0', str(int(lcd_height * (2/3))), '0', '0')
    elif idx == 1:
        print("1/2 page will be scrolled down")
        execute_scroll('0', str(int(lcd_height / 2)), '0', '0')
    elif idx == 5:
        print("Stay for 3 seconds without scrolling")
        time.sleep(3)
    else:
        print(str(idx-1),"pages will be scrolled down")
        time_slice = str(int(3000/(idx-1)))
        for i in range(idx-1):
            execute_scroll('0', str(lcd_height - 1), '0', '0', time_slice)

def click_single_clkkwd(dumpf, result_needed=False, kwds=None, origin="text", occur=1):
    if not os.path.isfile(dumpf):
        print("Failed to obtain UI dump for APK. Exiting UI interaction.")
        return False
    else:
        print("Dumpf file exists. Start processing next steps.")
    dump = xx.parse(dumpf)
    if dump == None:
        return False

    result = False
    nodes = dump.getElementsByTagName("node")
    occurrence = 0
    for elem in nodes:
        text = elem.getAttribute(origin)
        #print(text)
        coordinates = elem.getAttribute("bounds")
        x, y, xxe, yye = get_coordinates(coordinates)
        if (kwds == None and is_in_kwds(text)) or (kwds and text.lower() == kwds):
            occurrence += 1
            print("Find the click keyword:", text)
            if occurrence == occur:
                execute_click_middle(x, y, xxe, yye)
                result = True
                break
    if result_needed:
        return result


def close_translate_tab(dumpf):
    if dumpf == False:
        return False

    if not os.path.isfile(dumpf):
        print("Failed to obtain UI dump for APK. Exiting UI interaction")
        return False

    dump = xx.parse(dumpf)
    if dump is None:
        return False

    lcd_height = 640
    lcd_width = 320
    nodes = dump.getElementsByTagName("node")
    for elem in nodes:
        res_id = elem.getAttribute("resource-id")
        if res_id == "com.android.chrome:id/infobar_close_button":
            print("Close translate button......")
            # Proportional coordinates based on the new screen dimensions
            x_coord = int(lcd_width * (1244 / 1080))  # Adjust x-coordinate based on width
            y_coord = int(lcd_height * (2196 / 1920))  # Adjust y-coordinate based on height
            execute_click(str(x_coord), str(y_coord))
            return True
    return False

def access_domain(domain):
    dumpf = get_uidump()
    if not os.path.isfile(dumpf):
        print("Failed to obtaine UI dump for APK. Exiting UI interaction")
        return False

    dump = xx.parse(dumpf)
    if dump == None:
        return False

    nodes = dump.getElementsByTagName("node")
    for elem in nodes:
        res_id = elem.getAttribute("resource-id")
        if res_id == "com.android.chrome:id/search_box_text":
            search_bar = elem
            break
    coordinates = search_bar.getAttribute("bounds")
    x, y, xxe, yye = get_coordinates(coordinates)
    execute_click(x, y)
    time.sleep(2)
    enter_text('https://'+domain+'/')
    #time.sleep(2)
    execute_enter()

def is_in_kwds(k):
    word = k.lower()
    for keywd in clickkwds:
        #print(word, "in", keywd, "?")
        if word == keywd: #or word in keywd:
            return True
    return False

def is_search_bar_kwds(k):
    word = k.lower()
    for keywd in search_bar_kwds:
        if word == keywd or keywd in word:
            return True
    return False

def setup_chrome():
    for step_no in range(2):
        dumpf = get_uidump()
        actiondt = get_actions(dumpf)
        #print(len(actiondt))
        for k, v in actiondt.items():
            #print(k)
            if is_in_kwds(k):
                print("Trigger keywords click action. The kwd is", k)
                x, y, xxe, yye = v['xy']
                execute_click(x, y)
                break
        time.sleep(2)

#com.android.chrome:id/tab_switcher_button: [1104,84][1272,280]
#com.android.chrome:id/new_tab_button: [0,84][196,280]
def open_new_tab(domain):
    os.system("adb shell am start -n com.android.chrome/org.chromium.chrome.browser.ChromeTabbedActivity -d 'https://" + domain + "'")
    print(f"Navigated to https://{domain}")

def generate_interaction(profile=1, last_stay=False):
    #1: scroll 2: click 3: stay_and_read
    low_profile = [3,3,3,3,3,1,1,1,2,2]
    medium_profile = [3,3,3,2,2,2,2,1,1,1]
    high_profile = [3,3,1,1,1,2,2,2,2,2]

    if last_stay and profile == 1:
        idx = random.randint(5, 9)
    elif last_stay and profile == 2:
        idx = random.randint(3, 9)
    elif last_stay and profile == 3:
        idx = random.randint(2, 9)
    else:
        idx = random.randint(0, 9)

    if profile == 1:
        return low_profile[idx]
    elif profile == 2:
        return medium_profile[idx]
    else:
        return high_profile[idx]

def input_search_kwds(domain, dumpf):
    text_domains = ["google.com", "indeed.com", "baidu.com", "wikipedia.org", "google"]
    resid_domains = ["so.com", "duckduckgo.com", "haosou.com", "sogou.com", "soso.com"]
    if not os.path.isfile(dumpf):
        print("Failed to obtaine UI dump for APK. Exiting UI interaction")
        return False

    if domain == "booking.com":
        os.system('adb shell input keyevent 20')
        time.sleep(2)
        dumpf = get_uidump()
    dump = xx.parse(dumpf)
    if dump == None:
        return False
    if domain != "bing.com":
        nodes = dump.getElementsByTagName("node")
        for elem in nodes:
            text = elem.getAttribute("text")
            res_id = elem.getAttribute("resource-id")
            if domain == "booking.com":
                if text.lower() == "search":
                    print("Click search button for booking.com......")
                    coordinates = elem.getAttribute("bounds")
                    x, y, xxe, yye = get_coordinates(coordinates)
                    execute_click_middle(x, y, xxe, yye)
                    return
                else:
                    continue
            if domain == "indeed.com":
                execute_click('770', '570') #The keywords kept changing so coordinates are hard-coded
                time.sleep(2)
                execute_enter()
                return
            if domain in text_domains or "google" in domain:
                key = text
            elif domain in resid_domains:
                key = res_id
            if is_search_bar_kwds(key):
                print("Click search bar......")
                coordinates = elem.getAttribute("bounds")
                x, y, xxe, yye = get_coordinates(coordinates)
                execute_click_middle(x, y, xxe, yye)
                break

    idx = random.randint(0, len(searchkwds)-1)
    kwd = searchkwds[idx]
    enter_text(kwd)
    execute_enter()

def enter_username_password(domain, username="qcri2024@gmail.com", password="Qcriproxytest@42"):
    enter_text(username)
    if domain == "twitter.com":
        execute_enter()
        time.sleep(2)
        enter_text('testhy787')
        execute_enter()
        time.sleep(2)
        enter_text(password)
        execute_enter()
        return
    else:
        execute_tab()
        if domain == "facebook.com":
            time.sleep(1)
            execute_tab()
    time.sleep(2)
    enter_text(password)
    if domain == "facebook.com":
        time.sleep(1)
        execute_tab()
        time.sleep(1)
        execute_tab()
    time.sleep(2)
    execute_enter()


def login(domain, username="qcri2024@gmail.com", password="Qcriproxytest@42"):
    tb_account = "tb239769136454"
    special_domains=['taobao.com', 'twitter.com', 'pinterest.com', 'goodreads.com', 'quora.com', 'instagram.com']
    clickkwd_domains = ['linkedin.com']
    text_domains = ['twitter.com', 'instagram.com']
    resid_domains = ["taobao.com", "facebook.com", "pinterest.com", 'goodreads.com', 'linkedin.com']
    print("This webpage needs to log-in!!!!")
    time.sleep(5)
    if domain == "goodreads.com":
        #os.system('adb shell input keyevent 20') #press down
        os.system('adb shell input swipe 100 1000 100 80')
        time.sleep(2)
    dumpf = get_uidump()
    dumpf = get_uidump()
    if not os.path.isfile(dumpf):
        print("Failed to obtaine UI dump for APK. Exiting UI interaction")
        return False
    else:
        print("Dump file exists. Start processing next steps.")
    dump = xx.parse(dumpf)
    if dump == None:
        return False
    if domain in clickkwd_domains:
        if domain == "linkedin.com":
            result = click_single_clkkwd(dumpf, True)
        time.sleep(2)
        dumpf = get_uidump()
        dump = xx.parse(dumpf)
    if domain in special_domains:
        nodes = dump.getElementsByTagName("node")
        for elem in nodes:
            text = elem.getAttribute("text")
            coordinates = elem.getAttribute("bounds")
            x, y, xxe, yye = get_coordinates(coordinates)
            print(text)
            if is_login_kwd(text) and int(y)>280:
                print("Find the log-in keyword:", text)
                execute_click_middle(x, y, xxe, yye)
                time.sleep(2)
                dumpf = get_uidump()
                dump = xx.parse(dumpf)
                break
        if domain == "goodreads.com":
            time.sleep(2)
            dumpf = get_uidump()
            dump = xx.parse(dumpf)
            nodes = dump.getElementsByTagName("node")
            for elem in nodes:
                text = elem.getAttribute("text")
                if is_login_kwd(text):
                    print("Find the log-in keyword:", text)
                    coordinates = elem.getAttribute("bounds")
                    x, y, xxe, yye = get_coordinates(coordinates)
                    if int(y) <= 280:
                        continue
                    execute_click_middle(x, y, xxe, yye)
                    time.sleep(2)
                    dumpf = get_uidump()
                    dump = xx.parse(dumpf)
                    break
    #if domain == "facebook.com":
    #	dumpf = get_uidump()
    #	dump = xx.parse(dumpf)
    nodes = dump.getElementsByTagName("node")
    for elem in nodes:
        if domain in text_domains:
            text = elem.getAttribute("text")
        elif domain in resid_domains:
            text = elem.getAttribute("resource-id")
        else:
            enter_username_password(domain)
            return
        coordinates = elem.getAttribute("bounds")
        x, y, xxe, yye = get_coordinates(coordinates)
        if is_account_kwd(text) and int(y)>280:
            print("Find the account keyword:", text)
            execute_click_middle(x, y, xxe, yye)
            time.sleep(2)
            if domain == "taobao.com":
                enter_username_password(domain, username=tb_account)
            else:
                enter_username_password(domain)
            break
    if domain == "taobao.com":
        time.sleep(2)
        dumpf = get_uidump()
        dump = xx.parse(dumpf)
        nodes = dump.getElementsByTagName("node")
        for elem in nodes:
            text = elem.getAttribute("text")
            coordinates = elem.getAttribute("bounds")
            x, y, xxe, yye = get_coordinates(coordinates)
            if is_in_kwds(text) and int(y)>280:
                print("Find the click keyword:", text)
                execute_click_middle(x, y, xxe, yye)
                break
        time.sleep(2)
        execute_enter()
        dumpf = get_uidump()
        dump = xx.parse(dumpf)
        nodes = dump.getElementsByTagName("node")
        for elem in nodes:
            text = elem.getAttribute("text")
            if text == "滑块":
                print("Find the slideblock keyword:", text)
                coordinates = elem.getAttribute("bounds")
                x, y, xxe, yye = get_coordinates(coordinates)
                execute_scroll(x, y, '1440', y, '1000') #swipe slideblock
    if domain in ["facebook.com", "pinterest.com"]:
        time.sleep(2)
        dumpf = get_uidump()
        result = close_translate_tab(dumpf)
        if result:
            dumpf = get_uidump()
        dump = xx.parse(dumpf)
        nodes = dump.getElementsByTagName("node")
        for elem in nodes:
            text = elem.getAttribute("text")
            coordinates = elem.getAttribute("bounds")
            x, y, xxe, yye = get_coordinates(coordinates)
            if is_in_kwds(text) and int(y)>280:
                print("Find the click keyword(login):", text)
                execute_click_middle(x, y, xxe, yye)
                break

    return

#Low profile = [scroll 30%, click 20%, stay_and_read 50%]
#Medium profile = [scroll 30%, click 30%, stay_and_read 40%]
#High profile = [scroll 30%, click 50%, stay_and_read 20%]
#@timeout_decorator.timeout(int(sys.argv[3]))
def interact(domain, profile=1, searching=False):

    #random.seed(42)
    #For very short interaction duration
    if profile == 1:
        duration = random.randint(20, 300)
    elif profile == 2:
        duration = random.randint(20, 90)
    else:
        duration = random.randint(2, 20)
    print("Interaction time duration:", duration)
    if duration <= 5:
        time.sleep(duration)
        return

    start_time = datetime.now()
    time.sleep(5) #for the page to load
    if domain == "wayfair.com" or domain =="gucci.com/sg":
        execute_click('700', '1500')
        curr_time = datetime.now()
        time_left = int(duration-(curr_time-start_time).total_seconds())
        if time_left < 5:
            time.sleep(time_left)
            return
        else:
            time.sleep(5)

    if domain == "youtube.com":
        execute_click('140', '607')
    if domain == "vrbo.com":
        execute_page_down()
        execute_click('600','1200')
        curr_time = datetime.now()
        time_left = int(duration-(curr_time-start_time).total_seconds())
        if time_left < 5:
            time.sleep(time_left)
            return
        else:
            time.sleep(5)
    if domain == "drom.ru":
        execute_click('1300', '660')
        curr_time = datetime.now()
        time_left = int(duration-(curr_time-start_time).total_seconds())
        if time_left < 5:
            time.sleep(time_left)
            return
        else:
            time.sleep(5)
    dumpf = get_uidump()
    result = close_translate_tab(dumpf)
    curr_time = datetime.now()
    if (curr_time-start_time).total_seconds() >= duration:
        return
    if result:
        dumpf = get_uidump()
        curr_time = datetime.now()
        if (curr_time-start_time).total_seconds() >= duration:
            return
    if searching:
        input_search_kwds(domain, dumpf)
        curr_time = datetime.now()
        time_left = int(duration-(curr_time-start_time).total_seconds())
        if time_left <= 0:
            return
        elif time_left <= 5:
            time.sleep(time_left)
            return
        else:
            time.sleep(5)
        dumpf = get_uidump()
        curr_time = datetime.now()
        if (curr_time-start_time).total_seconds() >= duration:
            return
    actiondt = get_actions(dumpf)
    click_order = []
    if actiondt == False:
        actiondt = []
        print("actiondt: False")
    else:
        clickables = sort_actions(actiondt)
        click_order = choose_action(clickables)
    curr_time = datetime.now()
    if (curr_time-start_time).total_seconds() >= duration:
        return
    #trigger kwds click action
    if len(click_order) > 0:
        for tple in click_order:
            print("Performing click on: ", tple[0], tple[1])
            clickwords = tple[1].lower()
            print("Click button:", clickwords)
            perform_click(tple[0][0], tple[0][1], tple[0][2], tple[0][3], tple[0][4])
            curr_time = datetime.now()
            if (curr_time-start_time).total_seconds() >= duration:
                return
            time.sleep(2)
            curr_time = datetime.now()
            if (curr_time-start_time).total_seconds() >= duration:
                return
    if domain == "inps.it" and domain == "indeed.com":
        for rd in range(2):
            dumpf = get_uidump()
            dump = xx.parse(dumpf)
            curr_time = datetime.now()
            if (curr_time-start_time).total_seconds() >= duration:
                return
            nodes = dump.getElementsByTagName("node")
            for elem in nodes:
                text = elem.getAttribute("text")
                coordinates = elem.getAttribute("bounds")
                x, y, xxe, yye = get_coordinates(coordinates)
                if is_in_kwds(text):
                    curr_time = datetime.now()
                    if (curr_time-start_time).total_seconds() >= duration:
                        return
                    print("Find the click keyword:", text)
                    execute_click_middle(x, y, xxe, yye)
                    break
            time.sleep(2)
            curr_time = datetime.now()
            if (curr_time-start_time).total_seconds() >= duration:
                return
            if domain == "indeed.com":
                break
    dumpf = get_uidump()
    result = close_translate_tab(dumpf)
    curr_time = datetime.now()
    if (curr_time-start_time).total_seconds() >= duration:
        return
    if result:
        dumpf = get_uidump()
        curr_time = datetime.now()
        if (curr_time-start_time).total_seconds() >= duration:
            return
    if domain == "olx.in":
        dump = xx.parse(dumpf)
        curr_time = datetime.now()
        if (curr_time-start_time).total_seconds() >= duration:
            return
        nodes = dump.getElementsByTagName("node")
        for elem in nodes:
            text = elem.getAttribute("text")
            coordinates = elem.getAttribute("bounds")
            x, y, xxe, yye = get_coordinates(coordinates)
            if is_in_kwds(text):
                curr_time = datetime.now()
                if (curr_time-start_time).total_seconds() >= duration:
                    return
                print("Find the click keyword:", text)
                execute_click_middle(x, y, xxe, yye)
                break
        time.sleep(2)
        curr_time = datetime.now()
        if (curr_time-start_time).total_seconds() >= duration:
            return
    if domain == "vg.no":
        execute_click('700', '1600')
        curr_time = datetime.now()
        time_left = int(duration-(curr_time-start_time).total_seconds())
        if time_left < 5:
            time.sleep(time_left)
            return
        else:
            time.sleep(5)
    while True:
        perform_scroll()
        curr_time = datetime.now()
        if (curr_time-start_time).total_seconds() >= duration:
            return

@timeout_decorator.timeout(int(sys.argv[1])*60) #5mins
def browse_mixed_websites(domains, log, profile=1, mixed_type=True):
    seed = random.randint(1, 100)
    random.seed(seed)
    domains_num = len(domains)
    #is_first_domain = True
    accessed = []
    domain_idx = 0 #-1
    while True:
        domain_idx = random.randint(0, domains_num-1)
        #domain_idx += 1
        while domain_idx in accessed:
            domain_idx = random.randint(0, domains_num-1)
        accessed.append(domain_idx)
        domain_info = domains[domain_idx]
        domain = domain_info[0]
        domain_name = domain.split('.')[:-1]
        if len(domain_name) > 1:
            domain_name = "_".join(chunk for chunk in domain_name)
        else:
            domain_name = domain_name[0]
        print("Access domain:", domain, domain_idx)
        log.write("Access domain: " + domain +"\n")
        if domain == "douban.com":
            idx = random.randint(1, 5)
            cate = ['/movie', '/tv', '/book', '/group', '/music']
            domain = "m.douban.com"+cate[idx-1]
        elif domain == "jjwxc.net":
            domain = "m.jjwxc.net"
        elif domain == "autodesk.com.sg":
            domain = domain+"/products"
        elif domain == "weibo.cn":
            domain = "m.weibo.cn"
        elif domain == "aastocks.com":
            domain = "aastocks.com/tc/mobile/default.aspx"
        #if is_first_domain:
        #	access_domain(domain)
        #	is_first_domain = False
        #else:
        open_new_tab(domain)
        login_needed = domain_info[1]
        search_engine = domain_info[2]
        streaming = domain_info[3]
        if login_needed == "yes":
            log.write("Log-in in this domain......")
            login(domain)
        if search_engine == "yes":
            search_bar_needed = True
        else:
            search_bar_needed = False
        print("Wait for TRAFFIC COLLECTION......")
        start_time = datetime.now()
        try:
            interact(domain, profile, search_bar_needed)
        except TimeoutError as e:
            #print("Time limit is reached. Interaction with", domain_name, "ends......")
            raise e
        except Exception as e:
            log.write(domain_name+" => Error happend: "+str(e)+"\n")
            print(e)
            print("Interaction with", domain_name, "ends because of ERROR happened......")
            log.write("Interaction with "+domain_name+" ends because of ERROR happened......\n")
            #print("Sleep for exploring ERROR......")
            #time.sleep(10)
        curr_time = datetime.now()
        time_diff = int((curr_time-start_time).total_seconds())
        print("The time spent for "+domain_name+' is '+str(time_diff)+" seconds.")
        log.write("The time spent for "+domain_name+': '+str(time_diff)+" seconds.\n")
        #open_new_tab()
        #domain_idx += 1

def browse(collect_time=1*60, profile=1, mixed_type=True, file_path='res/Alexa_list', proxy_app=2):

    domains = get_domains(curdr+'/'+file_path)
    #print(domains)
    if len(domains) == 0:
        return


    for i in range(1):

        now = datetime.now()
        date_time_str = now.strftime("%d_%m_%Y_%H_%M_%S")
        log = open("data/logs/log_"+date_time_str+'_'+str(profile)+'.txt', "w+")

        pid = None
        activity = "low"
        if profile == 2:
            activity = "medium"
        elif profile == 3:
            activity = "high"
        stop_emu(pid)


        # Start emu again
        start_emu(PCAP_PATH, av='30')

        # Add setup for Magisk
        start_magisk()

        if mixed_type:
            print("Starting emulator for mixed domains with proxy app in background......")
            file_name = '/mixed_'+date_time_str+'_'+activity+'.pcap'
            pid = start_emu(PCAP_PATH+file_name, av='30', wipe_data=False)
            log.write(PCAP_PATH+'/mixed_'+str(i+28)+'_'+activity+'.pcap')
        else:
            print("Starting emulator for bg only traffic......")
            file_name = '/bg_'+date_time_str+'_'+activity+'.pcap'
            pid = start_emu(PCAP_PATH+file_name, av='30', wipe_data=False)
            log.write(PCAP_PATH+'/bg_'+str(i+28)+'_'+activity+'.pcap')


        # Setup remote capture app
        setup_remote_capture()

        print("Emulator ready for opening GOOGLE CHROME......")
        status, result = open_chrome()
        print("GOOGLE CHROME opening result => ", result)
        log.write("mixed domains\nOpening Chrome => result: "+str(result)+" => Emulator status: "+str(status)+"\n")
        time.sleep(4)
        if not result:
            if status:
                print("Attempts at opening GOOGLE CHROME failed!")
                log.write("Attempts at opening GOOGLE CHROME failed!\n")
            else:
                print("Emulator offline. Please check whether emulator is running!")
                log.write("Attempts at opening GOOGLE CHROME failed!\n")
        setup_chrome()
        try:
            if mixed_type:
                run_proxy(proxy_app, log)
            time.sleep(10)
            browse_mixed_websites(domains, log, profile, mixed_type)
        # time.sleep(collect_time)
        except TimeoutError as e:
            print(e)
            print(
                f"Traffic collection time limit {collect_time} secs is reached. Stop collecting traffic and close emulator......")
            log.write(
                f"Traffic collection time limit {collect_time} secs is reached. Stop collecting traffic and close emulator......\n")
        except KeyboardInterrupt:
            print("KeyboardInterrupt received. Finalizing remote capture.")
            log.write("KeyboardInterrupt received. Finalizing remote capture.\n")
        except Exception as e:
            print("Error happened:", e)
            log.write(f"Error happened: {e}\n")
        finally:
            # Finalize remote capture before stopping emulator
            finalize_remote_capture(file_name)
            # Then stop emulator
            os.system("pkill -f emulator")
            log.close()
            stop_emu(None)

            #stop_emu(None)

def run_proxy(proxy_app, log, proxy_file='res/apks_to_run'):
    f = open(curdr+'/'+proxy_file, 'r')
    file_exist = False
    lines = f.readlines()
    line = lines[proxy_app-1]
    line = line.rstrip().split(";")
    service = line[0] #Proxy/VPN service name
    proxy_hash = line[1].split("/")[2].split("##")[1].strip(".apk")
    proxy_path = line[1]
    pkg = line[2]
    mainactivity=line[3]
    target = '30'
    if not os.path.exists(curdr+proxy_path):
        print(curdr+proxy_path)
        print("Proxy file not available at path: ", curdr+proxy_path)
    else:
        file_exist = True
    if not file_exist:
        print("Proxy app was not found. No proxy app will run in background.")
        log.write("Proxy app was not found. No proxy app will run in background.\n")
        return
    print("Emulator ready for APK installation.....")
    result = runapk.main(curdr+proxy_path, pkg, mainactivity)
    print("APK install and execution result => ", result)
    log.write(service+"=>"+str(result)+"=>"+proxy_path+'\n')
    if result:
        print("Interaction with APP UI")
        iapk.main_intc() # APK Interaction module
        if proxy_app == 2:
            enter_text('qcri2024@gmail.com')
            time.sleep(10)
            execute_enter()
            time.sleep(5)
            enter_text('Qcriproxytest@42')
            time.sleep(10)
            execute_enter()
            time.sleep(2)
            iapk.main_intc()
            time.sleep(5)
            iapk.execute_click('1188', '182')
            time.sleep(5)
            iapk.execute_click('1350', '308')
            time.sleep(5)
            iapk.execute_click('1350', '308')
        #os.system('adb shell am force-stop com.android.chrome')
        print("Proxy app: ", service, "is running in the background")
        log.write("Proxy app: "+service+" is running in the background.\n")
    else:
        print("Skipping: ", service)
        log.write("Proxy app was skipped. No proxy app will run in background.\n")


def start_magisk():
        # Go to directory of rootAVD
        os.chdir(ROOTAVD_PATH)

        # Get command to install magisk
        command = "./rootAVD.sh ListAllAVDs.sh | tail | head -n 2 | tail -n 1"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Directly strip and clean the output without garbage characters
        install_command = result.stdout.strip()[4: -6]


        # Execute the outputted command
        if install_command:
                print(install_command)
                execution_result = os.popen(install_command).read().strip()
                print("Execution Result: ", execution_result)
        else:
                raise Exception("Command for installing magisk not working correctly")

        # Sleep for 60s to allow the installation to take place. Should have closed the emulator
        time.sleep(60)

        os.chdir(curdr)


def setup_remote_capture():
    # Install the APK
    apk_path = SCRIPT_DIR + "/apkfiles/com.emanuelef.remote_capture_78.apk"
    install_cmd = f"adb -s emulator-5554 install -g {apk_path}"
    os.system(install_cmd)

    # Launch the app
    launch_cmd = "adb shell am start -n com.emanuelef.remote_capture/.activities.MainActivity"
    os.system(launch_cmd)

    # Wait for app to launch
    time.sleep(2)

    # Click on skip
    execute_click('35', '604')
    time.sleep(2)
    # Click on three settings dots
    execute_click('300', '52')
    time.sleep(2)
    # Click on settings
    execute_click('160', '108')
    time.sleep(2)
    # Scroll down (swipe down)

    execute_scroll('160', '626', '160', '20', '1000')
    time.sleep(2)

    # Click on Capture as Root
    for i in range(2):
            execute_click('128', '519')
            time.sleep(2)

    # Going back to home screen
    execute_click('25', '50')
    time.sleep(2)
    # Clicking on "No Dump"
    execute_click('280', '466')
    time.sleep(2)
    # Clicking on "PCAP"
    execute_click('104', '399')
    time.sleep(2)
    # Clicking on "Ready"
    execute_click('152', '284')
    time.sleep(5)


    # Clicking on "OK"
    execute_click('222', '441')
    time.sleep(2)
    # Clicking on "OK" (Again)
    execute_click('285', '445')

    # Wait for a moment to ensure settings are applied
    time.sleep(2)

def finalize_remote_capture(file_name):
    # Bring app to foreground
    os.system("adb shell monkey -p com.emanuelef.remote_capture -c android.intent.category.LAUNCHER 1")
    time.sleep(2)
    # Stopping run of app
    execute_click('252', '49')
    time.sleep(1)
    # Click on "OK"
    execute_click('60', '370')
    time.sleep(1)
    # Pull file from Downloads
    os.system("adb pull /sdcard/Download/PCAPdroid ./")
    time.sleep(2)
    # Rename the file to the given file name. Assumes there's only one file in the directory
    os.system(f"mv PCAPdroid/* PCAPdroid/{file_name}")
    time.sleep(2)

    os.system("mv PCAPdroid/* " + PCAP_PATH)
    time.sleep(2)
    
    # Optionally, delete the files from the device
    print("Remote capture finalized and files moved.")

if __name__ == "__main__":
    print("USAGE: python3 browse_emu.py <time in mts: eg. 1/5/10/20> <user profile: eg. low/medium/high> <mixed traffic: eg. yes/no> <proxy app(enter # of app): eg.2(Bright Data)>")
    traffic_collection_time = int(sys.argv[1])*60
    profile = str(sys.argv[2]).upper()
    mixed = str(sys.argv[3]).upper()
    proxy_app = int(sys.argv[4])
    print("Each website will be visited and collected traffic for(seconds): ", traffic_collection_time)
    print("The user profile is: ", profile, "ACTIVITY user")
    print("The traffic is mixed or not:", mixed)
    print("The proxy app running in the background:", proxy_app)
    print("NOTE!!!: Run as root! Emulator is in /opt/androidsdk/ which may need root access.")
    if profile =="LOW":
        act_level = 1
    elif profile == "MEDIUM":
        act_level = 2
    else:
        act_level = 3

    if mixed == "YES":
        mixed_type = True
    else:
        mixed_type = False

    browse(collect_time=traffic_collection_time, profile=act_level, mixed_type=mixed_type, proxy_app=proxy_app)
