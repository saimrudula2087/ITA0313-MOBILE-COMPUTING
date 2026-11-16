"""Part I Task 3 - Launch sequence (Android) with cold/warm start executed by a dependency-checking simulator."""
import sys; sys.path.insert(0, "..")
from common import Capture, table

EXEC = [("Android (ART)", "DEX in APK", "ART loader / dex2oat", "Install (AOT/profile) + run time (JIT)"),
        ("iOS (ObjC/Swift)", "Mach-O native binary", "dyld", "Build time (already machine code)"),
        ("Windows (WinRT)", "Native .exe or .NET IL (.appx)", "NT loader / CLR", "Install (NGEN/.NET Native) or JIT at run time")]

# step: (name, component, purpose, requires)
STEPS = [
 ("1 Tap icon", "Launcher app", "Send start Intent", ["launcher"]),
 ("2 Resolve intent", "ActivityManager (system_server)", "Find target component", ["system_server"]),
 ("3 Process exists?", "ActivityManager", "Decide cold vs warm", ["system_server"]),
 ("4 Fork process", "zygote + kernel fork()", "Allocate PID, address space, COW preloaded ART", ["kernel_mm", "zygote"]),
 ("5 Init runtime", "ART", "Load dex/oat, set up heap & GC", ["process"]),
 ("6 Bind app thread", "ActivityThread", "Create Application, call onCreate", ["runtime"]),
 ("7 Create Activity", "ActivityThread", "Instantiate Activity, onCreate/onStart/onResume", ["app_object"]),
 ("8 Inflate+measure+draw", "View system / HWUI", "Build view tree, GPU draw", ["activity"]),
 ("9 First frame", "SurfaceFlinger", "Composite to display", ["frame"]),
]
PROVIDES = {1:"launcher",2:"intent",3:"decision",4:"process",5:"runtime",6:"app_object",7:"activity",8:"frame",9:"displayed"}
BASE = {"launcher","system_server","kernel_mm","zygote"}
COST = {1:5,2:8,3:1,4:35,5:60,6:40,7:30,8:45,9:16}

def run(kind):
    have = set(BASE); t = 0; rows = []
    if kind == "warm": have |= {"process","runtime","app_object"}
    for s in STEPS:
        n = int(s[0].split()[0])
        skip = kind == "warm" and n in (4,5,6)
        if not skip and not set(s[3]) <= have:
            rows.append((s[0], "BLOCKED", f"missing {set(s[3])-have}", 0)); break
        if skip: rows.append((s[0], "SKIPPED", "state already in memory", 0))
        else: t += COST[n]; rows.append((s[0], "RUN", s[2], COST[n])); have.add(PROVIDES[n])
    return rows, t

with Capture("p1_task3_output"):
    print("=== 3.1 Execution model ===")
    print(table(["Platform","Code delivered","Loader","Becomes machine code"], EXEC, [18,28,22,44]))
    print("\n=== 3.2 Launch sequence (Android) ===")
    print(table(["Step","Component","Purpose","Needs"], [(a,b,c,", ".join(d)) for a,b,c,d in STEPS], [24,32,44,24]))
    for kind in ("cold","warm"):
        rows, t = run(kind); print(f"\n=== 3.4 {kind.upper()} start ===")
        print(table(["Step","Status","Why","ms (model)"], rows, [24,8,38,10])); print(f"Total modelled time: {t} ms")
    print("\n=== 3.5 Dependency test: run step 6 without runtime ===")
    have = set(BASE) | {"process"}; print("Step 6 needs", STEPS[5][3], "-> present?", set(STEPS[5][3]) <= have, "=> BLOCKED: app code cannot run before ART init.")
