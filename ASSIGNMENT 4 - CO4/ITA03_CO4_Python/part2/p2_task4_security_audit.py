"""Part II Task 4 - Security audit engine: STRIDE threats -> mechanism -> residual risk -> verdict, plus predict/weaken/incident."""
import sys, copy; sys.path.insert(0, "..")
from common import Capture, table

APP = {"permissions": ["CAMERA","ACCESS_FINE_LOCATION","INTERNET"],
       "stores": {"auth_token": "keystore_aes", "local_db": "sqlcipher", "prefs": "encrypted_prefs"},
       "endpoints": [{"url": "https://api.health.example", "tls": True, "pinned": True}],
       "exported": {"MainActivity": True, "PatientDetailActivity": False}, "rooted_device_assumed": False}

def audit(app):
    T = []   # (threat, STRIDE, asset, vector, mechanism, result, residual)
    tok = app["stores"]["auth_token"]
    T.append(("Token theft by other app","I","Auth token","read app files",
              "UID sandbox + SELinux" + (" + Keystore" if tok=="keystore_aes" else ""),
              "Blocked" if tok=="keystore_aes" else "Exposed" , "Key extraction on compromised OS (accepted)" if tok=="keystore_aes" else "Plain token readable via run-as/backup"))
    T.append(("Local DB read on lost device","I","Local DB","pull DB file",
              "FBE + SQLCipher" if app["stores"]["local_db"]=="sqlcipher" else "FBE only",
              "Blocked" if app["stores"]["local_db"]=="sqlcipher" else "Partial","Unlocked-phone access (escalate: biometric re-auth)"))
    ep = app["endpoints"][0]
    res = "Blocked" if ep["tls"] and ep["pinned"] else ("Partial" if ep["tls"] else "Exposed")
    T.append(("MITM on API traffic","T/I","API traffic","rogue Wi-Fi proxy","TLS + cert pinning" if res=="Blocked" else ("TLS only" if ep["tls"] else "none (cleartext)"),res,"Pinned-cert rotation outage" if res=="Blocked" else "Attacker reads/alters PHI"))
    T.append(("Spoofed intent to internal screen","S/E","Exported activity","adb am start / malicious app","android:exported=false + permission",
              "Blocked" if not app["exported"]["PatientDetailActivity"] else "Exposed","None" if not app["exported"]["PatientDetailActivity"] else "Any app opens patient screen"))
    T.append(("Tampered APK / repackaging","T","App code","install modified APK","APK signing v3 + Play Protect","Blocked","Sideloaded re-signed app is a new identity"))
    T.append(("Over-privileged camera/location abuse","E","Camera, GPS","silent capture","Runtime permissions + indicator dots","Partial" if "CAMERA" in app["permissions"] else "Blocked","User may grant to a malicious update"))
    T.append(("Boot-time rootkit","T/E","OS integrity","modified system image","Verified boot (dm-verity)","Blocked","Bootloader-unlocked devices"))
    T.append(("Repudiation of record edits","R","Audit trail","deny changes","Server-side signed audit log","Partial","Needs server-side work outside app"))
    exposed = sum(t[5]=="Exposed" for t in T); partial = sum(t[5]=="Partial" for t in T)
    verdict = "FAIL - exposed assets" if exposed else ("CONDITIONAL PASS - residual risks documented" if partial else "PASS")
    return T, verdict

def show(title, app):
    T, v = audit(app); print(f"\n=== {title} ===")
    print(table(["Threat","STRIDE","Asset","Vector","Mechanism","Result","Residual risk"], T, [34,6,16,24,34,9,44]))
    print("VERDICT:", v); return v, T

with Capture("p2_task4_output"):
    print("Chain example: Threat(local data theft) -> Mitigation(Keystore-bound key + encrypted storage) -> Residual(key extraction on compromised OS: accepted)")
    v0,_ = show("4.1/4.2 Baseline audit", APP)
    print("\n=== 4.3 Predict-before-execute ===")
    print("Weaken: PatientDetailActivity android:exported=true.\nPrediction: asset 'Exported activity' becomes Exposed; most likely path = `adb shell am start -n pkg/.PatientDetailActivity` or malicious app Intent; verdict changes CONDITIONAL PASS -> FAIL.")
    weak = copy.deepcopy(APP); weak["exported"]["PatientDetailActivity"] = True
    v1,T1 = show("Observed after weakening", weak)
    print("Prediction check:", "CORRECT" if v1.startswith("FAIL") and any(t[2]=="Exported activity" and t[5]=="Exposed" for t in T1) else "WRONG")
    print("\n=== 4.4 Incident: 3rd-party SDK leaks device ID over HTTP ===")
    inc = copy.deepcopy(APP); inc["endpoints"].append({"url":"http://sdk.ads.example","tls":False,"pinned":False})
    T2,_ = audit(inc)
    print(table(["Question","Answer"],[("Asset/layer","Device identifier / network (transport) layer, app code layer"),
      ("Sandbox/permission contain it?","NO - SDK runs inside app's UID; INTERNET permission is legitimately held"),
      ("Detect where?","Static analysis (cleartext URLs, manifest), network capture (mitmproxy), runtime hook (OkHttp interceptor)"),
      ("Fix","Network Security Config cleartextTrafficPermitted=false (OS blocks HTTP), upgrade/remove SDK, use resettable ad-ID not hardware IDs"),
      ("Why sufficient","OS-enforced cleartext ban turns leak into connection failure; resettable ID limits linkability")],[30,100]))
    print("\n=== 4.5 Extension: biometrics + work profile ===")
    for x in ["Biometric: Keystore key with setUserAuthenticationRequired -> trust boundary moves to TEE/BiometricPrompt; add key attestation to prove hardware-backed key; threat: biometric spoof -> require CLASS 3.",
              "Work profile: second user (separate UID range, storage, Keystore); add threat 'cross-profile data leakage' - audit must check intent filters/clipboard/sharing policies.",
              "Remote wipe: new Elevation/DoS threat (wiper abuse) -> MDM-signed commands; audit logic needs per-profile asset inventory."]: print(" -",x)
