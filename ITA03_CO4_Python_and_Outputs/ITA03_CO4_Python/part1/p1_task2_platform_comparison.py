"""Part I Task 2 - Android vs iOS vs Windows comparison + message desk-check + challenge case."""
import sys; sys.path.insert(0, "..")
from common import Capture, table

MATRIX = [
 ("Kernel", "Linux, monolithic+loadable modules", "XNU (Mach + BSD hybrid), Darwin", "Windows NT hybrid kernel",
  "Driver crash on Android can panic kernel; Mach tasks isolate more"),
 ("Kernel API", "Linux syscalls via Bionic libc", "BSD syscalls + Mach traps", "NT native API (ntdll), Win32/WinRT on top",
  "Native crypto/socket code must be rebuilt per ABI"),
 ("Runtime", "ART (DEX; JIT+AOT; tracing GC)", "Objective-C/Swift native; ARC refcount", "WinRT/.NET (CLR) or native C++/WinRT",
  "GC pauses (Android) vs deterministic free (iOS)"),
 ("Framework", "Android SDK (system_server)", "Cocoa Touch / UIKit", "Windows Runtime APIs (UWP)",
  "Three UI/background APIs -> three code paths"),
 ("Isolation", "UID per app + SELinux", "Sandbox profile (Seatbelt) + entitlements", "AppContainer + capability SIDs",
  "Message DB path differs; all enforce per-app storage"),
 ("IPC", "Binder (/dev/binder)", "Mach ports / XPC", "ALPC / COM-WinRT brokers",
  "Push receiver reaches app via different broker"),
 ("Background push", "FCM -> Doze-exempt high-priority msg, Service", "APNs -> remote notification / NSE", "WNS -> background task trigger",
  "Only vendor push channel wakes a sleeping device on all three"),
]
TRACE = {
 "Android": ["Radio/NIC interrupt (hardware)", "Kernel net driver -> TCP socket; wakeup source holds wakelock",
   "Google Play services persistent FCM socket (system service) receives", "Framework: ActivityManager starts app process (zygote fork) if needed",
   "ART initialises runtime; FirebaseMessagingService.onMessageReceived() (app callback)"],
 "iOS": ["Radio interrupt (hardware)", "XNU network stack / driver", "apsd daemon (system service) receives APNs payload via XPC",
   "launchd spawns app in background; Objective-C/Swift runtime loads", "application:didReceiveRemoteNotification: (app callback, ~30 s budget)"],
}
CHALLENGE = {"cond": "App terminated by OS under memory pressure (lmkd on Android / jetsam on iOS)",
 "prediction": "Android delivers (FCM relaunches process); iOS delivers only if payload has content-available, and not if user force-quit.",
 "element": "Process-lifecycle manager: lmkd + zygote (Android) vs jetsam + launchd (iOS)",
 "trace": {"Android": ["lmkd kills app", "FCM message arrives at Play services", "ActivityManager forks from zygote", "onMessageReceived()"],
           "iOS": ["jetsam kills app", "apsd gets APNs", "launchd relaunches only if background-push allowed", "didReceiveRemoteNotification or silent drop"]},
 "correct": True}

with Capture("p1_task2_output"):
    print("=== 2.1 Problem model ===")
    for k, v in {"Input": "Android, iOS, Windows architectures", "Output": "Per-platform delivery feasibility + code-path count",
       "Objective": "Reliable background message receipt, secure, low battery", "Constraints": "Background exec, security, battery, latency",
       "Decision": "Native per platform vs shared core; which push channel", "Info needed": "Kernel, runtime, process model, isolation, IPC, push path"}.items():
        print(f"  {k:<12}: {v}")
    print("\n=== 2.2 Hypothesis ===")
    print("  The process/background-execution model (who may start an app process while idle) affects delivery most, because kernel type changes crash isolation but not whether a suspended app is woken.")
    print("\n=== 2.3 Comparison matrix ===")
    print(table(["Aspect", "Android", "iOS", "Windows", "Consequence for messaging app"], MATRIX, [10, 26, 26, 26, 38]))
    print("\n=== 2.4 Desk-check: incoming message, screen off ===")
    for p, steps in TRACE.items():
        print(f" [{p}]")
        for i, s in enumerate(steps, 1): print(f"   {i}. {s}")
    print("\n=== 2.5 Challenge ===")
    print(" Condition  :", CHALLENGE["cond"]); print(" Prediction :", CHALLENGE["prediction"]); print(" Element    :", CHALLENGE["element"])
    for p, s in CHALLENGE["trace"].items(): print(f"  [{p}] " + " -> ".join(s))
    print(" Prediction correct:", CHALLENGE["correct"])
