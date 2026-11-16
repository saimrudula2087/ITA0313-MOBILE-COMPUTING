# TASK 4: Applications of Mobile IP and Routing Requirements

print("APPLICATION OF MOBILE IP")
print("Example: Ambulance and emergency healthcare communication")

applications = [
    "Ambulance location tracking",
    "Communication between paramedics and hospitals",
    "Sending patient information to the hospital",
    "Continuous communication while travelling"
]

print("\\nApplications:")
for item in applications:
    print("-", item)

print("\\nRouting Requirements:")
requirements = {
    "Low delay": "Emergency messages should arrive quickly.",
    "Reliability": "Important data should reach its destination.",
    "Mobility support": "Communication should continue while moving.",
    "Security": "Patient information must be protected."
}

for key, value in requirements.items():
    print(key + ":", value)

print("\\nMobile IP maintains communication using Home Address and Care-of Address.")
