# TASK 1: Wireless Network Architecture and Mobility Analysis

network = {
    "Mobile1": ["Mobile2", "BaseStation"],
    "Mobile2": ["Mobile1", "Mobile3"],
    "Mobile3": ["Mobile2", "BaseStation"],
    "BaseStation": ["Mobile1", "Mobile3", "Gateway"],
    "Gateway": ["BaseStation"]
}

print("WIRELESS NETWORK ARCHITECTURE")
for device, connections in network.items():
    print(device, "->", ", ".join(connections))

print("\\nMobility Analysis")
print("Mobile1 moves from its old connection to a new access point.")
print("The network updates the connection and finds a new route.")
print("Result: Communication continues after handoff.")
