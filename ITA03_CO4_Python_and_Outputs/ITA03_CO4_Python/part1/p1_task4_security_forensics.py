"""Part I Task 4 - SecureNotes: model OS checks, run attack on original, repaired design, regression."""
import sys; sys.path.insert(0, "..")
from common import Capture, table

DEFECTS = [
 ("1 All permissions requested", "Permission model (least privilege)", "App holds CAMERA, SMS, CONTACTS...; any app-compromise inherits all", "Permission checks pass for everything"),
 ("2 Token in world-readable file", "Sandbox (UID + SELinux) / secure storage", "File mode 0644 lets other UIDs read; Keystore unused", "DAC allows 'other' read"),
 ("3 Updates from any source", "Code signing (same-cert rule)", "No signature continuity check; attacker APK can replace app", "PackageManager cannot verify publisher"),
 ("4 Plain HTTP", "Transport protection (TLS, network-security-config)", "Cleartext permitted; on-path attacker reads/modifies", "No confidentiality/integrity on wire"),
]

def os_allows(design, action):
    if action == "read_file_other_uid": return design["file_mode"] & 0o004 > 0
    if action == "install_update":      return (not design["verify_signature"]) or action == "signed_update"
    if action == "sniff_wifi":          return not design["tls"]
    if action == "use_permission_sms":  return "SMS" in design["permissions"]
    return False

ORIG = dict(permissions={"CAMERA","SMS","CONTACTS","LOCATION","INTERNET"}, file_mode=0o644, verify_signature=False, tls=False, token_in_keystore=False)
FIXED = dict(permissions={"INTERNET","CONTACTS"}, file_mode=0o600, verify_signature=True, tls=True, token_in_keystore=True)

def attack(design):
    log = []
    log.append("1. Malicious flashlight app installed from third-party store (own UID, no special perms).")
    if os_allows(design, "read_file_other_uid"):
        log.append("2. Malware reads /data/data/securenotes/token (mode 644) -> **CONFIDENTIALITY LOST HERE**.")
        log.append("3. Malware replays token to server over cafe Wi-Fi.")
    else:
        log.append("2. Read denied: kernel DAC/SELinux blocks cross-UID access (EACCES).")
    if os_allows(design, "sniff_wifi"):
        log.append("4. Attacker on same Wi-Fi sniffs HTTP -> token + notes in clear text (confidentiality lost).")
        log.append("5. Attacker modifies server response (integrity lost).")
    else:
        log.append("4. TLS handshake/cert check -> sniffed bytes are ciphertext; tamper detected.")
    return log

def contacts_flow(design, user_granted):
    return "CONTACTS" in design["permissions"] and user_granted

with Capture("p1_task4_output"):
    print("=== 4.1 Defects -> bypassed OS mechanism ===")
    print(table(["Decision", "Mechanism bypassed", "Why OS cannot protect", "Evidence in model"], DEFECTS, [28, 34, 52, 34]))
    print("\n=== 4.2 Attack trace on ORIGINAL design ===")
    for l in attack(ORIG): print("  ", l)
    print("\n=== 4.3 Repairs (minimal) ===")
    print(table(["Repair", "OS mechanism", "Where in architecture"], [
      ("Request only INTERNET + CONTACTS at runtime", "Runtime permission model", "L5 framework PackageManager/AppOps; kernel gid map"),
      ("Store token in Keystore-wrapped key, file mode 600", "Sandbox + hardware Keystore", "L1 kernel UID/SELinux; L2 TEE/StrongBox via keystore HAL"),
      ("Accept update only if same signing cert", "APK signature scheme v2/v3", "L5 PackageManager verify"),
      ("HTTPS, cleartextTrafficPermitted=false", "Network security config / TLS", "L3 BoringSSL, L5 framework")], [44, 30, 56]))
    print("\nAttack trace on FIXED design:")
    for l in attack(FIXED): print("  ", l)
    print("\n=== 4.4 Regression: user-agreed contacts read ===")
    for d, n in ((ORIG,"original"), (FIXED,"fixed")):
        print(f"  {n:<9}: contacts read after user grants permission -> {contacts_flow(d, True)}")
    assert contacts_flow(FIXED, True) and not contacts_flow(FIXED, False)
    print("  PASS: legitimate behaviour preserved; denied-permission case still blocked.")
