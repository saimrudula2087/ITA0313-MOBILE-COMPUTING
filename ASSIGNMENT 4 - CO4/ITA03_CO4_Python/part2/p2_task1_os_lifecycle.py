"""Part II Task 1 - OS resource-management model: lifecycle + LMK (oom_adj) simulator, predictions vs actual.
NOTE: simulation of Android's lmkd behaviour. On a device use the adb commands printed at the end for real evidence."""
import sys; sys.path.insert(0, "..")
from common import Capture, table

LAYERS = [("Android: Linux kernel","scheduler, mm, Binder driver, SELinux","/proc, ps"),
          ("HAL","vendor hardware interfaces","dumpsys media.camera"),
          ("Native libs + ART","Bionic, SQLite; DEX runtime","ps -A | grep zygote"),
          ("Framework","ActivityManager/PackageManager","dumpsys activity processes"),
          ("iOS: Core OS","XNU, launchd, security","documented (Apple Kernel Programming Guide)"),
          ("Core Services / Media / Cocoa Touch","Foundation, AV, UIKit","documented (App Programming Guide)")]
PROCESS = [("Android","zygote forks app_process (COW preloaded ART)","Binder (/dev/binder)","onCreate>onStart>onResume>onPause>onStop>onDestroy"),
           ("iOS","launchd spawns app; dyld loads Mach-O","XPC over Mach ports","Not running>Inactive>Active>Background>Suspended")]

# oom_adj scores (Android): lower = more important
OOM = {"foreground":0,"visible":100,"service":500,"cached_bg":900}
def lmk(app_state, mem_pressure):
    adj = OOM[app_state]
    thresholds = {"none":999,"moderate":900,"critical":500}   # kill procs with adj >= threshold
    killed = adj >= thresholds[mem_pressure]
    last_cb = {"foreground":"onResume","visible":"onPause","service":"onStop","cached_bg":"onStop"}[app_state]
    if killed and app_state=="cached_bg": last_cb="onStop (no onDestroy: process killed)"
    saved = "restored from Bundle (onSaveInstanceState ran before onStop)" if killed else "in memory, nothing to restore"
    if killed and app_state=="foreground": saved="LOST - process kill with no warning"
    return adj, ("KILLED" if killed else ("TRIMMED" if adj>=500 and mem_pressure!="none" else "ALIVE")), last_cb, saved

CASES = [("C1 foreground, normal memory","foreground","none","ALIVE"),
         ("C2 background 5 min, moderate pressure","cached_bg","moderate","KILLED"),
         ("C3 background service, critical pressure","service","critical","KILLED"),
         ("C4 foreground, critical pressure","foreground","critical","ALIVE")]

with Capture("p2_task1_output"):
    print("=== 1.1 Layer / process / IPC / lifecycle mapping ===")
    print(table(["Layer","Responsibility","Evidence source"], LAYERS,[34,40,40]))
    print(table(["OS","Process creation","IPC","Lifecycle"], PROCESS,[8,48,20,52]))
    print("\n=== 1.2 / 1.3 Predictions vs simulated actual ===")
    rows=[]
    for name,st,mem,pred in CASES:
        adj,act,cb,saved = lmk(st,mem)
        rows.append((name,f"oom_adj={adj}",pred,act,"MATCH" if pred==act else "MISMATCH",cb,saved))
    print(table(["Case","Score","Predicted","Actual","Result","Last callback","Saved state"],rows,[40,13,9,8,9,34,44]))
    print("\nMismatch interpretation: C3 predicted ALIVE-by-service-priority would be wrong at critical pressure; adj 500 >= threshold so lmkd kills it.")
    print("\n=== 1.4 Boundary case: rotation during background task ===")
    print("Selected because rotation destroys+recreates Activity; a task holding Activity ref leaks it / loses result. Expected defect: result delivered to dead Activity.")
    print("Fix: ViewModel holds task result; Activity observes LiveData; SavedStateHandle for process death.")
    print("\n=== adb commands for REAL evidence ===")
    for c in ["adb shell ps -A -o PID,NAME,ADJ | grep myapp","adb shell dumpsys activity processes | grep -A3 myapp","adb shell dumpsys meminfo com.example.myapp",
              "adb shell am send-trim-memory com.example.myapp COMPLETE","adb shell am kill com.example.myapp   # process death","adb logcat -s Lifecycle:D"]: print(" $",c)
