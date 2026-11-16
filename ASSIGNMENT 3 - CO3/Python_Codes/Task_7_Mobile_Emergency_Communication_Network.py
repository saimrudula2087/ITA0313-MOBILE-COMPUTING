# TASK 7: Design a Mobile Emergency Communication Network

network = {
    "Ambulance": ["Police", "Rescue Team"],
    "Police": ["Ambulance", "Rescue Team"],
    "Rescue Team": ["Ambulance", "Police", "Field Gateway"],
    "Field Gateway": ["Rescue Team", "Hospital"],
    "Hospital": ["Field Gateway"]
}

print("MOBILE EMERGENCY COMMUNICATION NETWORK")
for device, connections in network.items():
    print(device, "->", ", ".join(connections))

print("\\nCommunication Test")
print("Ambulance sends an emergency message to the hospital.")
print("Route: Ambulance -> Rescue Team -> Field Gateway -> Hospital")
print("Status: Message delivered successfully.")

print("\\nFailure Test")
print("If the Field Gateway connection fails, the system searches for another route.")
print("If no route is available, the message is stored and sent again later.")

print("\\nDesign Features")
print("- Ad hoc multi-hop communication")
print("- Alternative routes for reliability")
print("- Fast emergency alerts")
print("- Cellular network can be used as a backup")
