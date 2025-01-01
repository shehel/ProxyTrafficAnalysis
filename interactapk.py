'''
Automate user interactions post APP launch in the emulator
Created: 25th May 2023
@Author: Priyanka G. Dodia (pgdodia@hbku.edu.qa)
Qatar Computing Research Institute
'''

import os, sys
import xml.dom.minidom as xx
import time

global clickkwds
global earnappkwds
global signingoogle
global passgmail
global gmailusername
clickkwds = ["sure!","link device to my account","accept", "start", "i accept", "enter","i agree", "ok", "ok, i agree", "skip","allow","connect", "continue", "add", "next", "agree", "got it", "yes", "start using the app", "off", "i got it", "always", "agree & continue", "no thanks", "retry", "while using the app", "only this time", "change to pin code", "yes i am 18+", "add new proxy", "accept & continue", "log in with google", "never"] 
earnappkwds = ["earnapp.com", "sign in with google"]
signingoogle = False
gmailusername = "qcri2024@gmail.com" # Google account details for SIGN UP/LOG IN - Disable 2 Factor Authentication before sign in, if applicable
passgmail = "Qcriproxytest@42"

def get_uidump():
    os.system("rm window_dump.xml")
    print("1* Getting App UI dump file.....")
    curdr = os.getcwd()
    result = os.popen('adb shell uiautomator dump').read()
    if "ERROR" in result or "error" in result:
        return False
    result = os.popen('adb pull sdcard/window_dump.xml '+curdr+'/.').read()
    if "ERROR" in result or "error" in result:
        return False
    dumpf = curdr+"/window_dump.xml"
    return dumpf

# Process dump XML file, get the actions and coordinates
def get_actions(dumpf):
    actiondt = dict()
    ##print("Extracting action coordinates")
    # with open(dumpf, "r") as f:
    #     alllines = f.readlines()
    if not os.path.isfile(dumpf):
        print("Failed to obtaine UI dump for APK. Exiting UI interaction")
        return False

    dump = xx.parse(dumpf)
    if dump == None:
        return False

    #print(dump.nodeName)
    #print(dump.firstChild.tagName)
    #print(dump)
    nodes = dump.getElementsByTagName("node")
    for elem in nodes:
        actionname = elem.getAttribute("text")
        if len(actionname) == 0:
            actionname = elem.getAttribute("content-desc")
            if len(actionname) == 0:
                actionname = elem.getAttribute("resource-id")
        uitype = elem.getAttribute("resource-id") #switch_btn
        checkable = elem.getAttribute("checkable")
        clickable = elem.getAttribute("clickable")
        scrollable = elem.getAttribute("scrollable")
        longclickable = elem.getAttribute("long-clickable")
        coordinates = elem.getAttribute("bounds")
        enabled = elem.getAttribute("enabled")
        focusable = elem.getAttribute("focusable")
        ##print("NODE: ",actionname, "checkable: ", checkable," clickable: ",clickable," scrollable: ",scrollable," longclickable: ", longclickable)
        if len(actionname) >= 1 and not actionname in actiondt:
            if checkable == "true" or clickable == "true" or scrollable == "true" or longclickable == "true" or enabled == "true":
                ##print("Adding: ",actionname," to action list")
                actiondt[actionname] = {"xy": coordinates, "uitype": uitype, "checkable": checkable, "clickable": clickable, "scrollable": scrollable, "longclickable": longclickable, "enabled": enabled, "focusable": focusable}

    ##print("2* Actions available for UI interaction: ", actiondt.keys())
    return actiondt

def sort_actions(actiondt):
    ##print(actiondt)
    # click/checkwords: [xx,yy,xx_end,yy_end]
    clickables = dict()
    check = dict()
    # clickable & enabled
    for k, v in actiondt.items():
        clickable = v["clickable"]
        enabled = v["enabled"]
        checkable = v["checkable"]
        #cc = v["xy"].strip("[").strip("]").split("][")
        # Extract the bounds and add a check to ensure they are properly formatted
       # Extract the bounds and add a check to ensure they are properly formatted
        bounds_str = v["xy"]
        if not bounds_str or bounds_str == "[0,0][0,0]":
            #print(f"Skipping element with invalid bounds: {k}")
            continue

        #print(f"Processing bounds: {bounds_str} for {k}")

        try:
            cc = bounds_str.strip("[").strip("]").split("][")
            if len(cc) == 2:
                xx = cc[0].split(",")[0]  # x_start
                yy = cc[0].split(",")[1]  # y_start
                xxe = cc[1].split(",")[0] # x_end
                yye = cc[1].split(",")[1] # y_end
            else:
                raise ValueError(f"Unexpected bounds format for {k}: {bounds_str}")
        except Exception as e:
            print(f"Error processing bounds for {k}: {e}")
            continue



        buttontype = v["uitype"]
        if clickable and enabled:
            clickables[k] = [xx,yy,xxe,yye,buttontype]
            #print("Clickable: ",k, v["xy"])
        else:
            if checkable and enabled:
                check[k] = [xx,yy,xxe,yye, buttontype]
                #print("Checkable: ",k, v["xy"])
            if buttontype == "com.boostdev.volumebooster:id/sb_boost": # Oxylabs
                clickables[k] = [xx,yy,xxe,yye,buttontype]

    #{k: v for k, v in sorted(x.items(), key=lambda item: item[1])}
    return clickables, check

def is_in_kwds(k):
    word = k.lower()
    for keywd in clickkwds:
        #print(word, "in", keywd, "?")
        if word == keywd or word in keywd:
            return True
    return False

# Based on keywords on the page, detect if sign in required
def earnappsignin(k):
    global signingoogle
    if signingoogle == True:
        return
    if signingoogle == False:
        word = k.lower()
        if word in earnappkwds:
           signingoogle = word
           return
    if not signingoogle == True: # kwds on page matched partially
        word = k.lower()
        if (not word == signingoogle) and word in earnappkwds:
           signingoogle = True
           return
    return

def choose_action(clickables, checkables):
    click_order = []

    for k, v in clickables.items():
        if k == ' ':
            continue
        print("Clickable key: ", k)

        if is_in_kwds(k) or "button_next" in v[-1] or "com.boostdev.volumebooster:id/sb_boost" in v[-1]:
            print("Has click keywords")
            click_order += [(v, k)]

        earnappsignin(k) # EarnApp link device to Googleaccount?

    #print(click_order)
    click_order.sort(key=lambda x: (x[0][0],x[1][1]))
    print("Click order: ", click_order)
    return click_order

def execute_click(x, y):
    print("adb shell input mouse -d 0 tap "+x+" "+y)
    os.system("adb shell input tap "+x+" "+y)
    return

# Earnitapp: adb shell input swipe 475 1086 965 1282 300
def execute_scroll(x, y, xxe, yye, duration="300"):
    print("Attempting Button scroll/Swipe")
    nulllst = ["None", None]
    if not (x in nulllst and y in nulllst and xxe in nulllst and yye in nulllst):
        os.system("adb shell input swipe "+x+" "+y+" "+xxe+" "+yye+" "+duration)
    return

def execute_enter():
    os.system("adb shell input keyevent 66")
    return

def execute_tab():
    os.system("adb shell input keyevent 61")
    return

def enter_text(text):
    os.system('adb shell input keyboard text "'+text+'"')
    return

def perform_click(x, y, xxe, yye, acttype):
    nulllst = ["None", None]
    print("Performing click.......")
    if "switch_btn" in acttype or "swipe_to_login" in acttype or "oxylabsbooster" in acttype: #or "permissioncontroller" in acttype:
        print("Swiping switch button")
        if "oxylabsbooster" in acttype:
            execute_scroll(x, y, xxe, yye, "1")
        else:
            execute_scroll(x,y,xxe,yye)
        return True
    else:
        if not (x in nulllst and y in nulllst):
            #print("Tapping (x,y): ",x,y)
            # Updating coordinates to click in the middle of the button
            xx = int(x)+10
            yy = int(y)+10
            print("Tapping (x,y): ",xx,yy)
            execute_click(str(xx), str(yy))
            return True
        else:
            print("Clicking ENTER (coordinates not found)")
            execute_enter() # plain enter if failed to obtain x,y coordinates
            return False

def login(username=False, password=False):
    if username:
        enter_text(username)
        os.system("adb shell input keyevent 61") #Tab
        return "usernameentered"
    if password:
        enter_text(password)
        os.system("adb shell input keyevent 66") #Enter
    return

def signup():
    # Email username = "primash42"
    # Email password = "qcri@PM2023"
    password = "qcritest42"
    email = "primash42@outlook.com"
    name = "Priyanka"
    return email, password


# 'clicklimit': iteration limit of receiving empty clickables from UI dump of an APK before we stop UI interaction
def main_intc(clicklimit=20):
    iterbomb = 0
    global signingoogle
    global passgmail
    global gmailusername

    earnlogged = False

    # Default clicks = 10
    for i in range(0, 20):
        time.sleep(2)
        dumpf = get_uidump()
        if dumpf == False:
            print("Error in getting UI dump file. Exiting UI interaction module.")
            break
        actiondt = get_actions(dumpf)
        if actiondt == False:
            print("Error in getting UI dump file. Exiting UI interaction module.")
            break
        clickables, checkables = sort_actions(actiondt)
        clickelems = choose_action(clickables, checkables)
        clickedok = False
        if len(clickelems) > 0:
            for tple in clickelems:
                print("Performing click on: ", tple[0], tple[1])
                clickwords = tple[1].lower()

                if "com.boostdev.volumebooster:id/sb_boost" in clickwords:
                    perform_click(tple[0][0], tple[0][1], tple[0][2], tple[0][3],"oxylabsbooster")
                    return

                if signingoogle and not earnlogged:
                    print("Sign into Google is TurnedON")
                    print("Entering GMAIL USERNAME")
                    earnlogged = login(gmailusername,False)
                    print("Action status: ",earnlogged)
                    continue

                if signingoogle and earnlogged == "usernameentered":
                    if "next" in clickwords:
                         perform_click(tple[0][0], tple[0][1], tple[0][2], tple[0][3], tple[0][4])
                         time.sleep(4)
                         print("Entering GMAIL password")
                         login(False, passgmail)
                         print("Password Entered!")
                         signingoogle = False
                         earnlogged = False
                         return

                perform_click(tple[0][0], tple[0][1], tple[0][2], tple[0][3], tple[0][4])
                time.sleep(2)
        else:
            if iterbomb == clicklimit:
                print("Stopping UI interaction for APK......")
                return
            iterbomb += 1

    print("UI interaction complete.....Bye!")
    return

#dumpf = get_uidump()
#main_intc() # uncomment if you just want to run the interaction on the emulator

