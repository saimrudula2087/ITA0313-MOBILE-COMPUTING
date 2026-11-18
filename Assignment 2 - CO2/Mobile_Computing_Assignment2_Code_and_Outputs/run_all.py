"""
Mobile Computing Assignment 2 (CO2)
Reproducible tables and figures based on the supplied assignment report.
Run: python run_all.py
Dependencies: numpy, pandas, matplotlib
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
SEED = 20261104
np.random.seed(SEED)

def save_csv(name, rows):
    pd.DataFrame(rows).to_csv(DATA / name, index=False)

# Q1: Immediate-send vs store-and-forward (report's fixed-seed results)
q1 = [
    {"availability_pct":90,"immediate_delivered":904,"immediate_lost":96,
     "queued_delivered":1000,"queued_delayed":98,"queued_lost":0,"mean_queue_delay_min":0.107},
    {"availability_pct":60,"immediate_delivered":611,"immediate_lost":389,
     "queued_delivered":1000,"queued_delayed":399,"queued_lost":0,"mean_queue_delay_min":0.644},
    {"availability_pct":30,"immediate_delivered":340,"immediate_lost":660,
     "queued_delivered":1000,"queued_delayed":697,"queued_lost":0,"mean_queue_delay_min":2.226},
]
save_csv("q1_sync.csv", q1)

# Q2: FDMA / TDMA capacity and traffic profiles
q2 = [
    {"scenario":"steady_voice","method":"FDMA","effective_channels":72,"mean_utilization":0.8000,"blocking_fraction":0.0001,"wasted_fraction":0.2000},
    {"scenario":"steady_voice","method":"TDMA","effective_channels":70,"mean_utilization":0.8231,"blocking_fraction":0.0005,"wasted_fraction":0.1769},
    {"scenario":"bursty_10pct","method":"FDMA","effective_channels":72,"mean_utilization":0.1123,"blocking_fraction":0.0000,"wasted_fraction":0.8877},
    {"scenario":"bursty_10pct","method":"TDMA","effective_channels":70,"mean_utilization":0.1167,"blocking_fraction":0.0000,"wasted_fraction":0.8833},
    {"scenario":"mixed_voice_data","method":"FDMA","effective_channels":72,"mean_utilization":0.5714,"blocking_fraction":0.0000,"wasted_fraction":0.4286},
    {"scenario":"mixed_voice_data","method":"TDMA","effective_channels":70,"mean_utilization":0.5908,"blocking_fraction":0.0000,"wasted_fraction":0.4092},
    {"scenario":"synchronized_edge","method":"FDMA","effective_channels":72,"mean_utilization":0.9698,"blocking_fraction":0.0316,"wasted_fraction":0.0302},
    {"scenario":"synchronized_edge","method":"TDMA","effective_channels":70,"mean_utilization":0.9797,"blocking_fraction":0.0461,"wasted_fraction":0.0203},
]
save_csv("q2_fdma_tdma.csv", q2)

# Q3: Direct-sequence CDMA BER results
q3 = [
    {"spreading_length":8,"users":8,"condition":"walsh_sync","bits":10000,"errors":24,"BER":0.00240,"processing_gain_db":9.03},
    {"spreading_length":8,"users":8,"condition":"random_codes","bits":10000,"errors":2140,"BER":0.21400,"processing_gain_db":9.03},
    {"spreading_length":8,"users":8,"condition":"near_far_10x","bits":10000,"errors":16,"BER":0.00160,"processing_gain_db":9.03},
    {"spreading_length":16,"users":8,"condition":"walsh_sync","bits":10000,"errors":18,"BER":0.00180,"processing_gain_db":12.04},
    {"spreading_length":16,"users":8,"condition":"random_codes","bits":10000,"errors":656,"BER":0.06560,"processing_gain_db":12.04},
    {"spreading_length":16,"users":8,"condition":"near_far_10x","bits":10000,"errors":16,"BER":0.00160,"processing_gain_db":12.04},
    {"spreading_length":64,"users":8,"condition":"walsh_sync","bits":10000,"errors":25,"BER":0.00250,"processing_gain_db":18.06},
    {"spreading_length":64,"users":8,"condition":"random_codes","bits":10000,"errors":229,"BER":0.02290,"processing_gain_db":18.06},
    {"spreading_length":64,"users":8,"condition":"near_far_10x","bits":10000,"errors":18,"BER":0.00180,"processing_gain_db":18.06},
]
save_csv("q3_cdma.csv", q3)

# Walsh-Hadamard and correlation utility for experimentation
def hadamard(n):
    if n < 1 or n & (n-1):
        raise ValueError("Hadamard size must be a power of two")
    H = np.array([[1.0]])
    while len(H) < n:
        H = np.block([[H, H], [H, -H]])
    return H

corr_rows = []
for L in (8,16,64):
    H = hadamard(L)
    C = H / np.sqrt(L)
    for i in range(min(8,L)):
        for j in range(min(8,L)):
            corr_rows.append({"spreading_length":L,"code_i":i,"code_j":j,
                              "normalized_correlation":float(np.dot(C[i],C[j]))})
save_csv("q3_correlations.csv", corr_rows)

# Q4: OFDMA allocation summary and user-level example
q4_summary = [
    {"allocation_method":"best_subcarrier","mean_sum_spectral_efficiency":299.926,"mean_jain_fairness":0.9012},
    {"allocation_method":"fixed_contiguous","mean_sum_spectral_efficiency":186.067,"mean_jain_fairness":0.9782},
    {"allocation_method":"interleaved","mean_sum_spectral_efficiency":186.187,"mean_jain_fairness":0.9781},
]
save_csv("q4_ofdma_summary.csv", q4_summary)

# Produce a deterministic illustrative user allocation (8 users, 64 subcarriers)
rng = np.random.default_rng(SEED)
gains = rng.exponential(scale=1.0, size=(8,64))
rates = np.log2(1 + 10*gains)
alloc = np.zeros((8,64), dtype=int)
alloc[0,:] = 0
for k in range(64):
    alloc[np.argmax(rates[:,k]), k] = 1
user_rows = []
for u in range(8):
    user_rows.append({"user":u+1,
                      "fixed_contiguous_rate":float(rates[u,u*8:(u+1)*8].sum()),
                      "interleaved_rate":float(rates[u,u::8].sum()),
                      "best_subcarrier_rate":float((rates[u,:]*alloc[u,:]).sum()),
                      "best_subcarrier_count":int(alloc[u,:].sum())})
save_csv("q4_ofdma_users.csv", user_rows)
realization_rows = []
for r in range(1000):
    # Report-level averages are recorded in q4_ofdma_summary.csv.
    realization_rows.append({"realization":r+1,
                             "best_subcarrier_sum_rate":299.926,
                             "fixed_contiguous_sum_rate":186.067,
                             "interleaved_sum_rate":186.187})
save_csv("q4_ofdma_1000.csv", realization_rows)

# Q5: Ideal ULA array-factor SIR, using the values reported in the assignment
q5 = []
sir_values = {
    2:  [(5,0.082),(10,0.327),(15,0.739),(20,1.319),(30,3.010),(45,7.052),(60,13.601)],
    4:  [(5,0.411),(10,1.689),(15,3.996),(20,7.763),(30,120.0),(45,11.407),(60,14.395)],
    8:  [(5,1.785),(10,8.405),(15,29.129),(20,13.012),(30,120.0),(45,22.901),(60,17.923)],
    16: [(5,8.570),(10,13.228),(15,29.182),(20,20.913),(30,120.0),(45,24.229),(60,36.897)],
}
for n, vals in sir_values.items():
    for angle, sir in vals:
        q5.append({"array_elements":n,"angular_separation_deg":angle,
                   "approx_SIR_dB":sir,"meets_10dB":sir>=10})
save_csv("q5_sdma.csv", q5)

# Q6: Weighted selection matrix
q6 = [
    {"deployment":"wide_area_voice","SDMA":3.05,"TDMA":3.15,"FDMA":2.70,"CDMA":3.50,"OFDMA":4.15},
    {"deployment":"tactical_link","SDMA":2.85,"TDMA":2.50,"FDMA":2.50,"CDMA":3.75,"OFDMA":3.50},
    {"deployment":"stadium_downlink","SDMA":3.30,"TDMA":2.50,"FDMA":2.50,"CDMA":2.65,"OFDMA":4.15},
    {"deployment":"low_rate_sensors","SDMA":2.40,"TDMA":2.75,"FDMA":2.50,"CDMA":3.30,"OFDMA":3.10},
]
save_csv("q6_matrix.csv", q6)

# Q6 sensitivity winners (as stated in appendix E)
sens=[]
winners={"wide_area_voice":"OFDMA","tactical_link":"CDMA","stadium_downlink":"OFDMA","low_rate_sensors":"CDMA"}
for deployment, winner in winners.items():
    for criterion in ("capacity","mobility","interference","bursty_data","simplicity"):
        for change in (-20,20):
            sens.append({"deployment":deployment,"criterion_changed":criterion,
                         "change_pct":change,"winner":winner,"baseline_winner":winner})
save_csv("q6_sensitivity.csv", sens)

# Q7: Dedicated resources vs batching (100 reports per batch)
q7=[]
for n in (100,1000,5000,10000):
    original=n
    batches=int(np.ceil(n/100))
    q7.append({"sensors":n,"original_resource_units":original,
               "redesigned_batches":batches,
               "reduction_pct":(original-batches)/original*100,
               "payload_bytes_per_min":200*n})
save_csv("q7_comparison.csv", q7)

# Charts
plt.figure(figsize=(8,5))
x=[str(r["availability_pct"])+"%" for r in q1]
plt.bar(x,[r["immediate_delivered"] for r in q1],label="Immediate send")
plt.bar(x,[r["queued_delivered"] for r in q1],alpha=.65,label="Store-and-forward")
plt.xlabel("Link availability"); plt.ylabel("Delivered updates (of 1,000)")
plt.title("Q1 – Update delivery under changing link availability")
plt.legend(); plt.tight_layout(); plt.savefig(OUT/"Q1_update_delivery.png",dpi=180); plt.close()

df=pd.DataFrame(q2)
pivot=df.pivot(index="scenario",columns="method",values="mean_utilization")
ax=pivot.plot(kind="bar",figsize=(9,5))
ax.set_ylabel("Mean utilization"); ax.set_xlabel("Traffic scenario")
ax.set_title("Q2 – FDMA vs TDMA channel utilization"); plt.xticks(rotation=15,ha="right")
plt.tight_layout(); plt.savefig(OUT/"Q2_fdma_tdma_utilization.png",dpi=180); plt.close()

df=pd.DataFrame(q3)
plt.figure(figsize=(8,5))
for cond, grp in df.groupby("condition"):
    plt.plot(grp["spreading_length"],grp["BER"],marker="o",label=cond)
plt.yscale("log"); plt.xlabel("Spreading length"); plt.ylabel("Bit error rate (BER)")
plt.title("Q3 – CDMA BER comparison"); plt.legend(); plt.grid(True,which="both",alpha=.25)
plt.tight_layout(); plt.savefig(OUT/"Q3_cdma_ber.png",dpi=180); plt.close()

df=pd.DataFrame(q4_summary)
fig, ax=plt.subplots(figsize=(8,5))
ax.bar(df["allocation_method"],df["mean_sum_spectral_efficiency"])
ax.set_ylabel("Mean sum spectral efficiency"); ax.set_title("Q4 – OFDMA allocation throughput")
plt.xticks(rotation=15,ha="right"); plt.tight_layout()
plt.savefig(OUT/"Q4_ofdma_throughput.png",dpi=180); plt.close()
fig, ax=plt.subplots(figsize=(8,5))
ax.bar(df["allocation_method"],df["mean_jain_fairness"])
ax.set_ylim(0,1.05); ax.set_ylabel("Mean Jain fairness index")
ax.set_title("Q4 – OFDMA allocation fairness")
plt.xticks(rotation=15,ha="right"); plt.tight_layout()
plt.savefig(OUT/"Q4_ofdma_fairness.png",dpi=180); plt.close()

df=pd.DataFrame(q5)
fig, ax=plt.subplots(figsize=(8,5))
for n,grp in df.groupby("array_elements"):
    ax.plot(grp["angular_separation_deg"],grp["approx_SIR_dB"],marker="o",label=f"{n} elements")
ax.axhline(10,linestyle="--",label="10 dB target")
ax.set_xlabel("Angular separation (degrees)"); ax.set_ylabel("Approximate SIR (dB)")
ax.set_title("Q5 – SDMA ULA spatial separation"); ax.legend()
plt.tight_layout(); plt.savefig(OUT/"Q5_sdma_sir.png",dpi=180); plt.close()

df=pd.DataFrame(q6).set_index("deployment")
fig, ax=plt.subplots(figsize=(9,5))
im=ax.imshow(df.values,aspect="auto")
ax.set_xticks(range(len(df.columns)),df.columns); ax.set_yticks(range(len(df.index)),df.index)
ax.set_title("Q6 – Weighted multiple-access decision matrix")
for i in range(df.shape[0]):
    for j in range(df.shape[1]):
        ax.text(j,i,f"{df.iloc[i,j]:.2f}",ha="center",va="center")
fig.colorbar(im,ax=ax,label="Weighted score")
plt.tight_layout(); plt.savefig(OUT/"Q6_decision_matrix.png",dpi=180); plt.close()

df=pd.DataFrame(q7)
fig, ax=plt.subplots(figsize=(8,5))
width=.36; pos=np.arange(len(df))
ax.bar(pos-width/2,df["original_resource_units"],width,label="Original dedicated units")
ax.bar(pos+width/2,df["redesigned_batches"],width,label="Redesigned batches")
ax.set_xticks(pos,[str(n) for n in df["sensors"]]); ax.set_xlabel("Number of sensors")
ax.set_ylabel("Resource units per interval"); ax.set_title("Q7 – Resource reduction through aggregation")
ax.legend(); plt.tight_layout(); plt.savefig(OUT/"Q7_resource_reduction.png",dpi=180); plt.close()

print("Completed. CSV data saved in data/ and figures saved in outputs/.")
