import cereal.messaging as messaging

def main():
    # Create a messaging socket for longitudinalPlan, which includes lead car data
    sm = messaging.SubMaster(['longitudinalPlan'])

    print("Starting to monitor distance to the front vehicle (dRel)...\n")
    while True:
        # Update to get the latest data
        sm.update()

        # Check if lead car data is available
        if sm['longitudinalPlan'].leadOne.status:
            d_rel = sm['longitudinalPlan'].leadOne.dRel  # Distance to the lead vehicle in meters
            v_rel = sm['longitudinalPlan'].leadOne.vRel  # Relative velocity

            # Display the distance to the lead vehicle
            print(f"Distance to front vehicle (dRel): {d_rel:.2f} meters")
            print(f"Relative speed to front vehicle (vRel): {v_rel:.2f} m/s\n")

        else:
            print("No lead vehicle detected.\n")

        # Delay between checks (tune this delay as needed)
        time.sleep(1)

if __name__ == "__main__":
    main()