"""Part II Task 5 - DVFS vs Doze/Standby vs wakelock/batching. MODEL-BASED (documented power model), not measured on hardware."""
import sys; sys.path.insert(0, "..")
from common import Capture, table, plt, OUT

# modelled currents (mA) - assumptions stated, typical mid-range phone
CPU = {"LITTLE_low":40,"LITTLE_high":90,"BIG_high":420}; SLEEP=3; RADIO_ACTIVE=180; RADIO_TAIL_S=8; GPS=60
HOURS=8; MIN=HOURS*60

def baseline():     # app: GPS always, wakelock held, upload every 30 s, CPU on big core 25% duty
    mAh = (CPU["BIG_high"]*0.25 + CPU["LITTLE_low"]*0.75 + GPS)*HOURS + RADIO_ACTIVE*(RADIO_TAIL_S+2)/30*HOURS
    return dict(mAh=mAh, wakeups=HOURS*3600//30, wakelock_min=MIN, radio_active_min=MIN*(10/30))
def dvfs():         # Technique 1: governor keeps work on LITTLE low/high OPP; wake-ups unchanged
    mAh = (CPU["LITTLE_high"]*0.25 + CPU["LITTLE_low"]*0.75 + GPS)*HOURS + RADIO_ACTIVE*(RADIO_TAIL_S+2)/30*HOURS
    return dict(mAh=mAh, wakeups=HOURS*3600//30, wakelock_min=MIN, radio_active_min=MIN*(10/30))
def doze(wakelock=False):  # Technique 2: after screen off+stationary, maintenance windows only (grow 1,2,4... min->~ every 30 min)
    if wakelock: return baseline()    # partial wakelock exempts app: Doze benefit nullified
    windows = HOURS*2
    mAh = SLEEP*HOURS + windows*(RADIO_ACTIVE*(RADIO_TAIL_S+10)/3600) + windows*CPU["LITTLE_high"]*10/3600
    return dict(mAh=mAh, wakeups=windows, wakelock_min=windows*10/60, radio_active_min=windows*18/60)
def batching(batch=20, sensor_batch=True):  # Technique 3: WorkManager every 10 min, sensor FIFO batching, coalesced network
    uploads = MIN//10; 
    mAh = (CPU["LITTLE_low"]*0.05 + SLEEP*0.95 + (GPS*0.1 if sensor_batch else GPS))*HOURS + uploads*(RADIO_ACTIVE*(RADIO_TAIL_S+4)/3600)
    return dict(mAh=mAh, wakeups=uploads, wakelock_min=uploads*4/60, radio_active_min=uploads*12/60)
def exact_alarms(every_s=60):   # conflict: exact alarm each minute defeats batching
    wk = MIN; mAh = SLEEP*HOURS + wk*(RADIO_ACTIVE*(RADIO_TAIL_S+2)/3600) + wk*CPU["LITTLE_high"]*3/3600
    return dict(mAh=mAh, wakeups=wk, wakelock_min=wk*3/60, radio_active_min=wk*10/60)

with Capture("p2_task5_output"):
    print("Assumptions: 8 h shift, mid-range phone model: BIG 420 mA, LITTLE 40-90 mA, sleep 3 mA, radio 180 mA + 8 s tail, GPS 60 mA.")
    runs = [("Baseline (wakelock, 30 s uploads)",baseline()),("T1 DVFS/LITTLE cores",dvfs()),("T2 Doze + Standby",doze()),
            ("T3 WorkManager+sensor batching",batching()),("T2 + app holds partial wakelock (CONFLICT)",doze(True)),("T3 -> exact alarms every 60 s (CONFLICT)",exact_alarms())]
    print(table(["Configuration","Est. mAh/8h","Wake-ups","Wakelock min","Radio-active min"],
        [(n,f"{r['mAh']:.0f}",r['wakeups'],f"{r['wakelock_min']:.0f}",f"{r['radio_active_min']:.0f}") for n,r in runs],[42,12,10,13,17]))
    print("NOTE: T2 mAh excludes GPS (Doze suspends location), so it is NOT functionally equivalent to tracking in the other rows.")
    print("\n=== Power-state trace (conceptual, per technique) ===")
    for t,tr,trig,info,side in [
      ("T1 DVFS","LITTLE_low -> LITTLE_high -> BIG_high -> back","CPU utilisation crosses governor threshold","per-core load, thermal state","latency up when capped"),
      ("T2 Doze","ACTIVE -> LIGHT_IDLE -> DEEP_IDLE -> maintenance window -> DEEP_IDLE","screen off + unplugged + stationary","motion state, app standby bucket","deferred sync/alarms; GPS fixes stop"),
      ("T3 Batching","SLEEP -> job window (10 min) -> flush -> SLEEP","job constraints satisfied (network, idle)","queued records, last upload time","up to 10 min data latency")]:
        print(f" {t:<12} {tr}\n   trigger: {trig} | state kept: {info} | side-effect: {side}")
    print("\n=== Stress: can one layer defeat another? ===")
    b=doze()['mAh']; w=doze(True)['mAh']; e=exact_alarms()['mAh']; bt=batching()['mAh']
    print(f"YES. Doze {b:.0f} mAh -> with held wakelock {w:.0f} mAh ({w/b:.0f}x). Batching {bt:.0f} mAh -> exact alarms {e:.0f} mAh ({e/bt:.1f}x). App-layer behaviour overrides OS-layer idle control because the kernel honours the wakelock/alarm request.")
    print("\n=== Deployment decision ===")
    print(table(["Environment","Dominant consumers","Technique that matters","Reason (from results)"],[
      ("A always-on tracking","GPS + radio tails","T3 batching + sensor FIFO","T3 cuts wake-ups 20x (960->48) and keeps GPS data; Doze stops GPS"),
      ("B media/gaming","CPU/GPU + display","T1 DVFS/thermal governor","Wake-ups irrelevant; energy set by OPP and core choice"),
      ("C managed fleet, mixed OS","Policy variance","T2 buckets + MDM policy","Behaviour consistent via standby buckets/allow-lists; API differs by OS version")],[26,24,28,60]))
    fig,ax=plt.subplots(figsize=(9,3.6)); ax.barh([n for n,_ in runs],[r['mAh'] for _,r in runs],color=["#6b7280","#3b82f6","#22c55e","#22c55e","#ef4444","#ef4444"]); ax.invert_yaxis(); ax.set_xlabel("Estimated mAh / 8 h (model)"); plt.tight_layout(); plt.savefig(f"{OUT}/p2_task5_chart.png",dpi=110)
