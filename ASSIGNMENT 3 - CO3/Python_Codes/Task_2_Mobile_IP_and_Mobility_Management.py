# TASK 2: Mobile IP and Mobility Management

home_address = "10.0.0.25"
care_of_address = "172.16.1.20"
home_agent = "Home Agent"
foreign_agent = "Foreign Agent"

print("MOBILE IP REGISTRATION")
print("Permanent Home Address:", home_address)
print("Current Care-of Address:", care_of_address)
print("1. Mobile node moves to a visited network.")
print("2. Mobile node registers its Care-of Address with", home_agent)
print("3. Correspondent sends data to the Home Address.")
print("4. Home Agent tunnels the packet to", care_of_address)
print("5.", foreign_agent, "delivers the packet to the mobile node.")
print("\\nResult: The mobile node remains reachable while moving.")
