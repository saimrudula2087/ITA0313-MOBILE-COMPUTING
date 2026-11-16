"""Part II Task 6 - Battery-aware secure tracker: Policy[Battery][Network][Motion] -> (sampling, upload). Faithful simulation, real AES-GCM."""
import sys, os, json, random; sys.path.insert(0, "..")
from common import Capture, table, plt, OUT
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY = AESGCM.generate_key(256)          # stand-in for Android Keystore-held key
BATT = lambda pct, charging, saver: "CHARGING" if charging else ("SAVER" if saver or pct<=15 else ("LOW" if pct<=30 else "OK"))
NET  = lambda n: n   # WIFI / LTE / NONE
# Policy table: (BatteryState, NetState, Motion) -> (sampling_s, upload)
def policy(b, n, m, hot=False):
    base = {"MOVING":10,"STATIONARY":60}[m]
    mult = {"CHARGING":1,"OK":1,"LOW":2,"SAVER":6}[b]
    if hot: mult *= 2
    if n == "NONE": up = "QUEUE (encrypted)"
    elif b == "CHARGING" or n == "WIFI": up = "UPLOAD_BATCH_NOW"
    elif b == "SAVER": up = "DEFER_TO_CHARGE/WIFI"
    else: up = "UPLOAD_BATCH_EVERY_10_MIN"
    return base*mult, up
DEFAULT = ("OK","LTE","MOVING")  # initial state

E = dict(sample_mAh=0.0008, radio_wake_mAh=0.020, mAh_per_KB=0.0002)   # modelled: fixed cost per radio wake dominates
def cycle_energy(sampling_s, upload, window_s=3600):
    n = window_s//sampling_s; kb = n*0.1
    if upload.startswith("QUEUE") or upload.startswith("DEFER"): radio = 0
    elif upload.startswith("UPLOAD_BATCH_NOW"): radio = 1 if sampling_s>=10 else 1
    else: radio = window_s//600
    return n*E["sample_mAh"] + radio*E["radio_wake_mAh"] + (kb*E["mAh_per_KB"] if radio else 0), n

def encrypt(rec):
    nonce = os.urandom(12); ct = AESGCM(KEY).encrypt(nonce, json.dumps(rec).encode(), b"tracker-v1"); return nonce+ct

CONDS = [("1 Charging on Wi-Fi",100,True,"WIFI","MOVING",False),("2 80% battery on LTE, moving",80,False,"LTE","MOVING",False),
         ("3 20% battery, stationary, LTE",20,False,"LTE","STATIONARY",False),("4 Battery saver (10%)",10,False,"LTE","MOVING",False),
         ("5 No connectivity, 60%",60,False,"NONE","MOVING",False),("6 Device hot, 50%, Wi-Fi",50,False,"WIFI","MOVING",True)]

with Capture("p2_task6_output"):
    print("=== 6.1 Why battery level alone is insufficient ===")
    print("  Two states with 20% battery: (a) stationary on Wi-Fi, 0 queued -> sample rarely, upload nothing;  (b) moving, no network, 400 queued -> sample normally, queue encrypted, flush when network returns.")
    print("  Needed state: battery %, charging, network type, last_upload, queue length, temperature, motion.")
    print("\n=== 6.3 Prototype: 6 operating conditions (1 h window) ===")
    rows=[]; results={}
    for name,pct,chg,net,mot,hot in CONDS:
        b=BATT(pct,chg,False); s,u=policy(b,net,mot,hot); e,n=cycle_energy(s,u); ct=encrypt({"lat":12.9,"lon":80.0,"t":0})
        results[name]=(s,u,e); rows.append((name,f"{b}/{net}/{mot}",f"{s}s",u,f"{e:.4f}","AES-256-GCM, %d B"%len(ct)))
    print(table(["Condition","Policy state","Sampling","Upload decision","mAh/h","Encrypted before store/send"],rows,[32,26,9,28,8,26]))
    print(f"Default state: {DEFAULT}")

    print("\n=== 6.4 Validation vs always-on baseline (1 Hz sampling, upload each sample) ===")
    base = 3600*E["sample_mAh"] + 3600*E["radio_wake_mAh"]
    val=[]
    for name in list(results)[:3]:
        s,u,e = results[name]; hand = (3600//s)*E["sample_mAh"] + (1 if u.startswith("UPLOAD_BATCH_NOW") else (6 if "10_MIN" in u else 0))*E["radio_wake_mAh"] + ((3600//s)*0.1*E["mAh_per_KB"] if not (u.startswith("QUEUE") or u.startswith("DEFER")) else 0)
        val.append((name,f"{hand:.4f}",f"{e:.4f}","MATCH" if abs(hand-e)<1e-9 else "DIFF",f"{base/e:.0f}x less than baseline {base:.2f}"))
    print(table(["Condition","Hand calc mAh","Prototype mAh","Result","vs always-on"],val,[32,14,14,8,36]))
    print("  Independent hand calculation (sample count x cost + radio wakes x fixed wake cost) agrees -> code matches the formula. LIMITATION: both use the same cost constants, so this validates the logic, not the energy model itself (needs device measurement).")

    print("\n=== 6.5 Scalability: batch vs immediate upload ===")
    srows=[]; pts=[]
    for n in (100,1000,10000):
        evals=n; wake_batch=max(1,n//100); wake_imm=n
        mah_b=n*E["sample_mAh"]+wake_batch*E["radio_wake_mAh"]+n*0.1*E["mAh_per_KB"]; mah_i=n*E["sample_mAh"]+wake_imm*E["radio_wake_mAh"]+n*0.1*E["mAh_per_KB"]
        srows.append((n,evals,f"{wake_batch} (imm: {wake_imm})",f"queued<=100, {mah_b:.2f} mAh (imm {mah_i:.2f})")); pts.append((n,mah_b,mah_i))
    print(table(["Records","Policy evals","Wake-ups","Queue / energy"],srows,[10,13,22,42]))
    print("  Batching removes ~99% of radio wakes (fixed 0.02 mAh each) but sampling energy and data-volume energy scale with record count, so high-frequency tracking stays costly.")
    print("\n=== 6.6 Emergency requirement (not implemented) ===")
    print("  Property changed: latency bound (batch minutes -> seconds) now dominates energy. Batching/defer policy violates it. Investigate priority-based policy: EMERGENCY state overrides battery state; foreground service + high-priority push; server-side fleet manager. Trade-off: more radio wakes (+heat, battery), higher location-privacy exposure, higher server/cost.")
    print("\n=== 6.7 Reflection (<=150 words) ===")
    print("  In my prototype, deferring uploads in battery saver (condition 4) cost only 0.048 mAh/h, yet that same rule would break emergency delivery. Condition 5 (no network) still spent 0.288 mAh/h because sampling energy is unaffected by upload policy, and batching cut radio wakes ~99% without reducing sampling or data-volume cost. Each feature optimises one cost under assumptions about motion, connectivity and latency; when those change, it stops being optimal, so no single OS or power feature suits every app.")
    fig,ax=plt.subplots(1,2,figsize=(11,3.6)); names=[r[0].split(' ',1)[0] for r in rows]; ax[0].bar(names,[float(r[4]) for r in rows],color="#3b82f6"); ax[0].set_title("mAh per hour by condition (1-6)")
    ns=[p[0] for p in pts]; ax[1].plot(ns,[p[1] for p in pts],marker="o",label="batched"); ax[1].plot(ns,[p[2] for p in pts],marker="o",label="immediate"); ax[1].set_xscale("log"); ax[1].legend(); ax[1].set_title("Energy vs load (mAh)"); plt.tight_layout(); plt.savefig(f"{OUT}/p2_task6_chart.png",dpi=110)
