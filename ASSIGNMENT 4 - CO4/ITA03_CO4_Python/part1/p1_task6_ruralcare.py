"""Part I Task 6 - RuralCare: constraint table, offline store + idempotent sync, desk-check, 3 adverse tests."""
import sys, uuid, hashlib, random; sys.path.insert(0, "..")
from common import Capture, table

CONSTRAINTS = [
 ("A Android", "ART (Kotlin)", "App sandbox, Keystore AES-GCM, FBE, remote wipe", "WorkManager, Doze, batching, battery-saver hook", "SQLCipher/Room encrypted", "LTE/Wi-Fi, intermittent"),
 ("B iPhone", "Swift/ObjC, ARC", "Sandbox, Keychain/Secure Enclave, Data Protection", "BGTaskScheduler, Low Power Mode", "Core Data + file protection", "LTE/Wi-Fi, intermittent"),
 ("C Feature phone", "J2ME/JME MIDP, or WML browser", "No sandbox guarantees; RMS only, optional app-level AES", "None; short sessions only", "RMS (~100 KB)", "GPRS/SMS only"),
]
RETAINED = ["record_uuid (idempotency key)", "device_id + monotonic seq_no (ordering, gap detection)", "created_at (device clock + server offset)",
            "sync_state {PENDING,SENT,ACKED}", "payload SHA-256 (corruption detect)", "last_acked_seq (resume point)", "key_version (decrypt after rotation)"]

class Server:
    def __init__(self): self.store = {}
    def receive(self, rec, corrupt=False):
        body = rec["payload"] if not corrupt else rec["payload"][:-1] + b"X"
        if hashlib.sha256(body).hexdigest() != rec["sha"]: return "NACK_CORRUPT"
        if rec["uuid"] in self.store: return "ACK_DUP"       # idempotent: no duplicate stored
        self.store[rec["uuid"]] = rec; return "ACK"

class Device:
    def __init__(self, cls="A"):
        self.cls, self.q, self.seq, self.wiped, self.key = cls, [], 0, False, "K1"
    def capture(self, text):
        self.seq += 1; enc = bytes(b ^ 0x5A for b in text.encode())    # stand-in for AES-GCM
        self.q.append(dict(uuid=str(uuid.uuid4()), seq=self.seq, payload=enc, sha=hashlib.sha256(enc).hexdigest(), state="PENDING", enc=(self.cls != "C")))
    def sync(self, server, drop_after=None, corrupt_at=None):
        sent = 0
        for r in [x for x in self.q if x["state"] != "ACKED"]:
            if drop_after is not None and sent >= drop_after: return "INTERRUPTED"
            res = server.receive(r, corrupt=(corrupt_at == r["seq"])); sent += 1
            if res.startswith("ACK"): r["state"] = "ACKED"
            else: return f"STOPPED:{res}@seq{r['seq']}"
        return "COMPLETE"

with Capture("p1_task6_output"):
    print("=== Stage 3: constraint table ===")
    print(table(["Class","Runtime","Security","Power controls","Offline storage","Connectivity"], CONSTRAINTS, [14,20,40,34,24,22]))
    print("\nRetained for loss/duplication safety:"); [print("  -", x) for x in RETAINED]

    print("\n=== Stage 5: Class A, 6 h offline, battery 20%, phone lost, never synced ===")
    d = Device("A"); [d.capture(f"patient{i}") for i in range(1, 7)]
    print(" 1. 6 h offline: 6 records captured, AES-GCM encrypted, state=PENDING")
    print(" 2. Battery 20% -> power-saver policy: GPS/sensor interval x3, no sync attempts (offline)")
    print(" 3. Phone lost -> screen lock + FBE: key bound to unlock; Keystore key unusable without PIN")
    print(" 4. Admin issues remote wipe; executes on next connectivity; 5 failed PINs -> key invalidated")
    print(f" EXPOSED: ciphertext only (plaintext readable: {any(not r['enc'] for r in d.q)}) | LOST: {len(d.q)} unsynced records on device (not on server) | RECOVERABLE: none from device; re-collect via follow-up visit; audit log on server shows last seq")

    print("\n=== Stage 6: Adverse conditions ===")
    print("\n[Adv 1] Sync interrupted after 3 of 6, then resumed")
    s = Server(); d = Device("A"); [d.capture(f"p{i}") for i in range(6)]
    print("  predict: resume sends only 3 remaining; no duplicates")
    print("  run1:", d.sync(s, drop_after=3), "| run2:", d.sync(s), "| server records:", len(s.store), "(expected 6) ->", "PASS" if len(s.store)==6 else "FAIL")

    print("\n[Adv 2] Lost ACK: server stored record, device never saw ACK, retransmits")
    s = Server(); d = Device("A"); d.capture("x"); s.receive(d.q[0]); r = d.sync(s)
    print("  predict: server returns ACK_DUP, stores 1 copy; result:", r, "| stored:", len(s.store), "->", "PASS" if len(s.store)==1 else "FAIL")

    print("\n[Adv 3] Corruption mid-transfer at seq 2")
    s = Server(); d = Device("A"); [d.capture(f"p{i}") for i in range(4)]
    print("  predict: sync halts at seq 2, seq1 ACKED, seq 2-4 stay PENDING; run1:", d.sync(s, corrupt_at=2), "| states:", [r["state"] for r in d.q])
    print("  retry clean:", d.sync(s), "| stored:", len(s.store), "->", "PASS" if len(s.store)==4 else "FAIL")

    print("\n[Adv 4] Class C: no secure storage")
    c = Device("C"); c.capture("child immunisation record")
    print(f"  record encrypted? {c.q[0]['enc']}  -> ASSUMPTION FAILS: RMS is readable if phone lost.")
    print("  Refinement: Class C stores NO patient identifiers; only coded ID + visit data, app-level AES key derived from PIN (PBKDF2), sync via SMS gateway/WML form after each record, delete after ACK.")
    print("\nCritical decision: idempotency key + per-record ACK. Surviving: Adv1-3. Needing refinement: Adv4.")
