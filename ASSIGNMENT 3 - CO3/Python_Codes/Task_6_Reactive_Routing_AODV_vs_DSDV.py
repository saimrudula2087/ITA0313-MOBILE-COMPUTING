# TASK 6: Reactive Routing and Protocol Comparison (AODV vs DSDV)

print("AODV ROUTE DISCOVERY")
source = "Node A"
destination = "Node D"

print("Source:", source)
print("Destination:", destination)
print("1. Source broadcasts Route Request (RREQ).")
print("2. Destination sends Route Reply (RREP).")
print("3. Route is established: A -> B -> C -> D")
print("4. Data packets are transmitted.")

print("\\nLink failure:")
print("AODV sends a Route Error (RERR) and searches for a new route.")

print("\\nPROTOCOL COMPARISON")
print("{:<15} {:<25} {:<25}".format("Feature", "DSDV", "AODV"))
print("-" * 65)
comparison = [
    ("Type", "Proactive", "Reactive"),
    ("Route setup", "Before sending", "When required"),
    ("Control", "Periodic updates", "RREQ, RREP, RERR"),
    ("Initial delay", "Usually low", "May be higher")
]
for row in comparison:
    print("{:<15} {:<25} {:<25}".format(*row))
