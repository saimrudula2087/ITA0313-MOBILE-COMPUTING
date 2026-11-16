# TASK 3: Cellular Networks versus Ad Hoc Wireless Networks

print("CELLULAR NETWORK VS AD HOC NETWORK")
print("-" * 72)
print("{:<18} {:<25} {:<25}".format("Parameter", "Cellular Network", "Ad Hoc Network"))
print("-" * 72)

rows = [
    ("Infrastructure", "Uses base stations", "No fixed infrastructure"),
    ("Communication", "Through base station", "Direct or multi-hop"),
    ("Routing", "Network controlled", "Distributed routing"),
    ("Mobility", "Handoff between cells", "Routes change with nodes"),
    ("Example", "Mobile phone network", "Rescue team network")
]

for row in rows:
    print("{:<18} {:<25} {:<25}".format(*row))

print("\\nConclusion: Cellular networks provide wide coverage.")
print("Ad hoc networks are useful when fixed infrastructure is unavailable.")
