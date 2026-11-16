# TASK 5: Proactive Routing Protocol - DSDV

# Simple example of a DSDV routing table
routing_table = {
    "A": {"Destination": "A", "Next Hop": "-", "Hops": 0},
    "B": {"Destination": "B", "Next Hop": "B", "Hops": 1},
    "C": {"Destination": "C", "Next Hop": "B", "Hops": 2},
    "D": {"Destination": "D", "Next Hop": "B", "Hops": 3}
}

print("DSDV ROUTING TABLE AT NODE A")
print("{:<15} {:<15} {:<10}".format("Destination", "Next Hop", "Hops"))
print("-" * 40)

for destination, details in routing_table.items():
    print("{:<15} {:<15} {:<10}".format(
        details["Destination"], details["Next Hop"], details["Hops"]))

print("\\nTopology change: Link between B and C fails.")
print("DSDV updates its routing table and sequence numbers.")
print("Result: Routes are maintained before data transmission.")
