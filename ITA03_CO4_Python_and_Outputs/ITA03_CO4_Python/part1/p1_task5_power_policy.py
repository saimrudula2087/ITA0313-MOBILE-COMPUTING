"""Part I Task 5 - power-state machine, push wake-up, battery saver; energy compared with always-awake app."""
import sys; sys.path.insert(0, "..")
from common import Capture, table, plt, OUT

mA = {"ACTIVE": 250, "IDLE": 60, "SUSPENDED": 3, "SUSP_WAKE": 120}   # modelled average current (mA)
TRANS = [
 ("ACTIVE", "IDLE", "screen off + 30 s no input", "CPU low OPP, radio demoted; foreground app paused; allowed: services holding wakelock"),
 ("IDLE", "SUSPENDED", "no wakelock held for 60 s", "CPU cores offline in deep sleep, RAM self-refresh; allowed: none (alarm/modem wake only)"),
 ("SUSPENDED", "ACTIVE", "power key / incoming call", "CPUs resume, full cpufreq; all allowed"),
 ("SUSPENDED", "SUSP_WAKE", "high-priority push interrupt from modem", "one core resumes 5 s; allowed: push receiver only"),
 ("SUSP_WAKE", "SUSPENDED", "handler done / 5 s timeout", "release wakelock, return to deep sleep"),
]
def simulate(hours=8, app_wakelock=False, pushes=0, saver=False):
    scale = 0.7 if saver else 1.0
    if app_wakelock: return mA["IDLE"] * hours * scale          # never reaches SUSPENDED
    wake_h = pushes * 5 / 3600
    return (mA["SUSPENDED"] * (hours - wake_h) + mA["SUSP_WAKE"] * wake_h) * scale

with Capture("p1_task5_output"):
    print("=== 5.1 Power-state transition table ===")
    print(table(["From", "To", "Entry/exit condition", "Hardware/kernel action + allowed work"], TRANS, [10, 10, 34, 70]))
    print("\n=== Energy over 8 h screen-off (mAh) ===")
    rows = [("Original: CPU wakelock held forever", simulate(app_wakelock=True)),
            ("Policy: deep sleep, no pushes", simulate()),
            ("5.2 Push-based wake-up, 40 urgent pushes", simulate(pushes=40)),
            ("5.2 Wrong fix: polling wakelock 10 s/min", 8*60*(10/60*mA['SUSP_WAKE']+50/60*mA['SUSPENDED'])/60),
            ("5.3 Battery saver (<=15%) + 40 pushes", simulate(pushes=40, saver=True))]
    print(table(["Scenario", "mAh"], [(a, f"{b:.1f}") for a, b in rows], [44, 8]))
    print("\n5.2 Unsafe/insufficient part: 'only apps holding wakelocks run in IDLE' - an app cannot receive while SUSPENDED; fix = modem push interrupt (SUSP_WAKE), app must stop holding a permanent wakelock/polling.")
    print("5.3 Battery saver @15%: KERNEL - cap cpufreq to LITTLE cores, 30% lower max freq; RUNTIME - defer JIT/GC compaction, expedite job batching; APP - sensor rate 1 Hz->0.2 Hz, no background sync.")
    print("Trade-off: slower UI animations & delayed non-urgent sync; acceptable as it extends remaining runtime and urgent pushes still work.")
    fig, ax = plt.subplots(figsize=(8, 3.5)); ax.barh([r[0] for r in rows], [r[1] for r in rows], color="#3b82f6")
    ax.set_xlabel("mAh over 8 h"); ax.invert_yaxis(); plt.tight_layout(); plt.savefig(f"{OUT}/p1_task5_chart.png", dpi=110)
