"""Part I Task 1 - Architecture review: diagnose draft note, validate repaired Android spec."""
import sys; sys.path.insert(0, "..")
from common import Capture, table

DRAFT = {
 "D1 'hardware at bottom, apps at top'": ("Missing layers: no drivers, HAL, native libs, framework services, runtime",
     "Engineer cannot tell where drivers live or how apps reach a camera/modem."),
 "D2 'a kernel sits in the middle'": ("Kernel type/duties unspecified (monolithic/hybrid/micro; scheduler, VM, IPC, drivers)",
     "Cannot predict fault isolation, driver-crash impact or IPC cost."),
 "D3 'kernel runs the applications'": ("Kernel schedules processes; it does not execute app code via the runtime",
     "Conflates scheduler with runtime; process-creation path (zygote/launchd) lost."),
 "D4 'compiled and executed by runtime'": ("No code form (DEX/native), JIT/AOT/interpreter, or translation time stated",
     "Cannot estimate start-up time, storage footprint or memory model."),
 "D5 'secure using permissions'": ("Grantor, time (install/run), enforcement point (framework check + kernel UID/SELinux) absent",
     "Cannot test whether a denied permission is really blocked."),
 "D6 'saves battery when needed'": ("No trigger (screen-off, idle, 15%), mechanism (DVFS, suspend, Doze) or owning component",
     "Not testable: 'when needed' has no threshold."),
 "D7 'framework to build apps'": ("No app/OS boundary or IPC path (Binder, syscalls) defined",
     "Cannot determine trust boundary or privilege of API calls."),
}
ANDROID = [
 ("L6 Applications", "User apps (Activity/Service/Receiver) in own sandbox process, own Linux UID",
  "Lifecycle callbacks, Intents", "L5 Framework (Binder calls)"),
 ("L5 Application Framework", "system_server: ActivityManager, PackageManager, PowerManager; permission check point #1",
  "Kotlin/Java SDK APIs", "L4 ART + L3 libs via Binder /dev/binder"),
 ("L4 Android Runtime (ART)", "Runs DEX: interpreter+JIT+profile-guided AOT; GC; zygote-forked processes",
  "Managed execution, JNI", "L3 native libs / L1 syscalls"),
 ("L3 Native libraries", "Bionic libc, SQLite, BoringSSL, Skia, media",
  "C/C++ APIs (NDK/JNI)", "L1 kernel syscalls"),
 ("L2 HAL", "Vendor HIDL/AIDL modules for camera, sensors, radio",
  "Stable hardware interfaces", "L1 kernel drivers"),
 ("L1 Linux kernel (monolithic)", "Scheduler, VM, Binder driver, SELinux MAC + UID DAC (point #2), wakelocks/suspend, cpufreq (DVFS), drivers",
  "System-call interface", "L0 Hardware"),
 ("L0 Hardware", "big.LITTLE CPU, RAM, radio, sensors, battery", "Registers/interrupts", "-"),
]
def validate(spec):
    errs = []
    for name, resp, exposes, deps in spec:
        for f, v in (("responsibility", resp), ("exposes", exposes), ("depends_on", deps)):
            if not v.strip(): errs.append(f"{name}: missing {f}")
    txt = " ".join(" ".join(l) for l in spec).lower()
    for must in ("kernel", "art", "selinux", "permission check", "cpufreq", "wakelock"):
        if must not in txt: errs.append(f"component not located: {must}")
    return errs
DEFENCE = ("The specification names each layer, states what it exposes upward and depends on downward, and places the kernel (L1), "
 "runtime (L4), enforcement points (L5 permission check, L1 SELinux/UID) and power control (PowerManager L5; wakelocks and cpufreq L1) "
 "at explicit addresses. Every claim is testable: an engineer can verify a denied permission by tracing the Binder call and kernel check. "
 "Marketing text gives no thresholds, owners or interfaces.")
with Capture("p1_task1_output"):
    print("=== TASK 1.1  Diagnosis of draft note ===")
    print(table(["Statement", "Technical deficiency", "Why it cannot be built/evaluated"], [(k, v[0], v[1]) for k, v in DRAFT.items()], [30, 50, 50]))
    print(f"\nDeficiencies identified: {len(DRAFT)} (required >= 5) -> {'PASS' if len(DRAFT)>=5 else 'FAIL'}")
    print("\n=== TASK 1.2  Repaired Android layered specification ===")
    print(table(["Layer", "Responsibility", "Exposes above", "Depends on below"], ANDROID, [26, 48, 26, 28]))
    e = validate(ANDROID); print("\nSpec validator:", "PASS - all layers complete, key components located" if not e else e)
    print(f"\n=== TASK 1.3  Defence ({len(DEFENCE.split())} words, limit 100) ===")
    print(DEFENCE, "\n->", "PASS" if len(DEFENCE.split()) <= 100 else "FAIL")
