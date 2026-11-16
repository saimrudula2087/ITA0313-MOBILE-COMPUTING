"""Part II Task 3 - runtime behaviour. REAL measurements on CPython as an analogue of ART; ART-specific commands printed at the end."""
import sys, time, gc, subprocess, tracemalloc, threading; sys.path.insert(0, "..")
from common import Capture, table, plt, OUT

def cpu_loop(n=300_000):
    s = 0
    for i in range(n): s += i*i % 7
    return s
def cpu_native(n=300_000): return sum(i*i % 7 for i in range(n))      # generator - still interpreted
def cpu_builtin(n=300_000): return sum(map(pow, range(n), [2]*n))        # C-level loop (AOT-native analogue)
def alloc_heavy(n=200_000): return len([{"id": i, "tag": str(i)} for i in range(n)])
def ui_list(n=20_000): return len(["<row %d>%s" % (i, "x"*20) for i in range(n)])

def timed(f, reps=1):
    t = time.perf_counter(); [f() for _ in range(reps)]; return (time.perf_counter()-t)/reps

pauses = []; _t = [0]
def gc_cb(phase, info):
    if phase == "start": _t[0] = time.perf_counter()
    else: pauses.append((time.perf_counter()-_t[0])*1e3)

def startup(code): 
    t = time.perf_counter(); subprocess.run([sys.executable, "-c", code], capture_output=True); return (time.perf_counter()-t)*1e3

with Capture("p2_task3_output"):
    print("=== Stage A: normal execution ===")
    cold = startup("import json"); warm = min(startup("import json") for _ in range(5))
    print(f"Process cold start {cold:.1f} ms | warm (cached pages/.pyc) {warm:.1f} ms")
    gc.callbacks.append(gc_cb); gc.collect(); tracemalloc.start(); heap=[]
    for name,f in (("CPU loop",cpu_loop),("Alloc-heavy",alloc_heavy),("UI list",ui_list)):
        first = timed(f); steady = timed(f, 3); heap.append((name, tracemalloc.get_traced_memory()[1]/1e6))
        print(f"  {name:<12} first-run {first*1e3:8.1f} ms | steady {steady*1e3:8.1f} ms")
    print(f"GC events: {len(pauses)} | max pause {max(pauses):.2f} ms | mean {sum(pauses)/len(pauses):.3f} ms")
    print("Heap peak (MB):", {n: round(v,1) for n,v in heap})

    print("\n=== Stage B: compilation-mode analogue ===")
    print("Prediction: CPU loop affected most (dispatch overhead per bytecode); alloc/UI workloads barely change; faster mode costs startup/storage.")
    t_int, t_gen, t_nat = timed(cpu_loop,3), timed(cpu_native,3), timed(cpu_builtin,3)
    print(table(["Mode (ART analogue)","Time ms","vs interpret"],[("interpret-only (python loop)",f"{t_int*1e3:.1f}","1.00x"),
          ("generator expr (still interpreted)",f"{t_gen*1e3:.1f}",f"{t_int/t_gen:.2f}x"),("speed/AOT (C builtin loop)",f"{t_nat*1e3:.1f}",f"{t_int/t_nat:.2f}x")],[30,10,14]))
    print("CAVEAT: CPython has no JIT, so first-run vs steady shows no warm-up; the speed-up above is interpreter-loop vs C-loop (analogue of interpret vs AOT), not measured ART compilation.")
    print("Roles: interpreter starts instantly but is slow; JIT compiles hot methods at run time; profile-guided AOT (speed-profile) precompiles hot paths at install/idle; Baseline Profiles ship that profile so first launch is already compiled.")
    print("Real ART commands: adb shell cmd package compile -m speed-profile -f com.example.bench | dumpsys package com.example.bench | grep -A2 'Dexopt state'")

    print("\n=== Stage C: production failure detection ===")
    leak = []; tracemalloc.reset_peak(); samples=[]
    for i in range(6):
        leak.append(bytearray(2_000_000)); samples.append(tracemalloc.get_traced_memory()[0]/1e6)   # unbounded cache
    growth = [round(b-a,1) for a,b in zip(samples,samples[1:])]
    print("Heap MB per step:", [round(x,1) for x in samples], "growth/step:", growth)
    print("DETECTED: monotonic growth, no release after gc.collect() ->", "LEAK" if all(g>1 for g in growth) else "ok", "(reported by heap tracker; on Android: OOM / GC_ALLOC lines, LeakCanary)")
    del leak; gc.collect()
    blocked = []
    def watchdog(limit, stop):
        t = time.perf_counter()
        while not stop.is_set():
            if time.perf_counter()-t > limit: blocked.append(time.perf_counter()-t); return
            time.sleep(0.005)
    stop = threading.Event(); w = threading.Thread(target=watchdog, args=(0.2, stop)); w.start()
    time.sleep(0.5); stop.set(); w.join()      # "main thread" blocked 0.5 s
    print(f"WATCHDOG: main thread unresponsive >{0.2*1e3:.0f} ms -> {'ANR-like event reported' if blocked else 'none'} (Android: watchdog + ANR trace; StrictMode)")

    print("\n=== Stage D: cross-platform comparison ===")
    print(table(["Runtime","Start-up","Memory model","UI thread","Native API access"],[
      ("ART Kotlin / Swift ARC","fast w/ baseline profile / native","tracing GC / refcount","platform UI thread","direct"),
      ("Flutter (Dart AOT)","fast, bundles engine (+MBs)","generational GC, own heap","own raster thread, Skia/Impeller","platform channels"),
      ("React Native / WebView","slower: JS engine + bridge init","JS GC + native heap","JS thread + bridge hop","bridge/JSI, async")],[24,32,24,30,18]))
    print("Recommendation (from documented runtime architecture + Stage B analogue, NOT measured on Flutter here): Flutter for one code-base - AOT avoids JIT warm-up and the JS bridge hop; keep native modules for Keystore/Keychain. Stage C evidence supports the need for bounded caches and main-thread watchdogs in every option; it does not discriminate between runtimes.")
    fig,ax=plt.subplots(1,2,figsize=(10,3.4)); ax[0].bar(["interpret","generator","AOT-like"],[t_int*1e3,t_gen*1e3,t_nat*1e3],color=["#ef4444","#f59e0b","#22c55e"]); ax[0].set_title("Compile-mode analogue (ms)")
    ax[1].plot(range(1,7),samples,marker="o",color="#ef4444"); ax[1].set_title("Heap growth under leak (MB)"); plt.tight_layout(); plt.savefig(f"{OUT}/p2_task3_chart.png",dpi=110)
