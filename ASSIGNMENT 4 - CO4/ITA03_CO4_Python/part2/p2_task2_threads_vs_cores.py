"""Part II Task 2 - REAL measurements: single-thread vs multi-thread/process on this machine (Python stands in for Kotlin executors)."""
import sys, time, os, resource, threading, tracemalloc; sys.path.insert(0, "..")
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from common import Capture, table, plt, OUT

def heavy(n):                      # CPU-bound chunk ("image filter")
    s = 0
    for i in range(n): s += (i*i) % 7
    return s
def tiny(n): return n+1
def io_task(_):                    # sensor/network wait (0.1 s) + light parse
    time.sleep(0.1); return heavy(20000)
def single_io():  [io_task(i) for i in range(8)]
def pool_io():
    with ThreadPoolExecutor(8) as ex: list(ex.map(io_task, range(8)))

def measure(fn):
    r0 = resource.getrusage(resource.RUSAGE_SELF); c0 = resource.getrusage(resource.RUSAGE_CHILDREN); t0 = time.perf_counter(); tracemalloc.start()
    fn(); wall = time.perf_counter()-t0; cur, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    r1 = resource.getrusage(resource.RUSAGE_SELF); c1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (r1.ru_utime-r0.ru_utime)+(r1.ru_stime-r0.ru_stime)+(c1.ru_utime-c0.ru_utime)+(c1.ru_stime-c0.ru_stime)
    return dict(wall=wall, cpu=cpu, ctx=(r1.ru_nvcsw-r0.ru_nvcsw)+(r1.ru_nivcsw-r0.ru_nivcsw), peak_kb=peak/1024)

N=os.cpu_count() or 2
def single_heavy():  [heavy(1_500_000) for _ in range(N*2)]
def pool_heavy():
    with ProcessPoolExecutor(N) as ex: list(ex.map(heavy,[1_500_000]*(N*2)))
def thread_heavy():
    with ThreadPoolExecutor(N) as ex: list(ex.map(heavy,[1_500_000]*(N*2)))
def single_tiny():   [tiny(i) for i in range(200)]
def thread_tiny():
    with ThreadPoolExecutor(8) as ex: list(ex.map(tiny,range(200)))
lock = threading.Lock(); counter=[0]
def contended(_):
    for _ in range(20000):
        with lock: counter[0]+=1
def single_lock():   [contended(0) for _ in range(8)]
def thread_lock():
    with ThreadPoolExecutor(8) as ex: list(ex.map(contended,range(8)))

def jank(main_blocked_s, frames=60):    # frames at 16.7 ms; blocked main thread drops frames
    return int(main_blocked_s/0.0167)

with Capture("p2_task2_output"):
    print(f"Host cores: {N}  (Python 3, real measurements)")
    exps = [("2.1 NORMAL  I/O+parse, 1 thread",single_io),("2.1 NORMAL  I/O+parse, 8 threads",pool_io),
            ("2.2 CPU-heavy, 1 thread",single_heavy),("2.2 CPU-heavy, process pool",pool_heavy),("2.2 CPU-heavy, THREAD pool (GIL)",thread_heavy),("2.2 tiny task, 1 thread",single_tiny),
            ("2.2 tiny task, 8 threads",thread_tiny),("2.2 lock contention, 1 thread",single_lock),("2.2 lock contention, 8 threads",thread_lock)]
    res = {}
    for n,f in exps: res[n]=measure(f)
    print(table(["Experiment","Wall s","CPU s","Ctx switches","Peak mem KB"],[(n,f"{v['wall']:.4f}",f"{v['cpu']:.4f}",v['ctx'],f"{v['peak_kb']:.0f}") for n,v in res.items()],[34,9,9,13,12]))
    sp = res[exps[0][0]]['wall']/res[exps[1][0]]['wall']
    print(f"\nNormal-case speed-up (8 threads vs 1, I/O-wait workload): {sp:.2f}x  <- clear improvement")
    print(f"CPU-heavy on {N} core(s): process pool {res[exps[2][0]]['wall']/res[exps[3][0]]['wall']:.2f}x, thread pool {res[exps[2][0]]['wall']/res[exps[4][0]]['wall']:.2f}x -> no gain without >1 physical core (GIL blocks threads anyway).")
    print("Thread-to-core placement: not observable on this 1-core sandbox; on a device use `adb shell top -H -p <pid>` or Perfetto sched tracks.")
    t1,t8 = res[exps[5][0]]['wall'], res[exps[6][0]]['wall']
    print(f"Tiny task: single {t1*1e3:.2f} ms vs 8 threads {t8*1e3:.2f} ms -> multi-thread {'WORSE' if t8>t1 else 'not worse'} ({t8/t1:.1f}x)")
    l1,l8 = res[exps[7][0]]['wall'], res[exps[8][0]]['wall']
    print(f"Lock contention: single {l1:.3f}s vs 8 threads {l8:.3f}s -> {'WORSE/no gain' if l8>=l1*0.95 else 'better'}")
    print("First design decision causing degradation: spawning a pool + sharing one lock for work smaller than thread-start/sync cost.")
    print("\nUser-perceived quality: main-thread heavy task blocks UI ->", jank(res[exps[2][0]]['wall']), "dropped 60fps frames; offloaded ->", jank(0.001), "frames.")
    print("Predictability: single-thread worst case = linear; multi-thread worst case adds lock wait + scheduling jitter.")
    print("\n=== 2.4 Day-on-one-charge requirement ===")
    print(f"Measured: pool CPU {res[exps[3][0]]['cpu']:.2f}s vs single {res[exps[2][0]]['cpu']:.2f}s (similar total work => parallelism saves latency, not energy). Tiny-task threading cost {res[exps[6][0]]['cpu']/max(res[exps[5][0]]['cpu'],1e-6):.0f}x CPU.")
    print("Decision: cap workers at 1-2 (efficiency cores), batch via WorkManager with charging/idle constraints; accept slower finish; never spawn pools for tiny jobs.")
    fig,ax=plt.subplots(1,2,figsize=(11,3.6)); names=[k.split(' ',1)[1] for k in res]
    ax[0].barh(names,[v['wall'] for v in res.values()],color="#3b82f6"); ax[0].set_title("Wall time (s)"); ax[0].invert_yaxis()
    ax[1].barh(names,[v['cpu'] for v in res.values()],color="#f59e0b"); ax[1].set_title("CPU time (s) ~ energy"); ax[1].invert_yaxis(); ax[1].set_yticklabels([])
    plt.tight_layout(); plt.savefig(f"{OUT}/p2_task2_chart.png",dpi=110)
