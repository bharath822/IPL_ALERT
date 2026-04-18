import os
import requests
from twilio.rest import Client

FILE_NAME = "last_alerted_inning.txt"

def trigger_call(reason, inning_name):
    client = Client(os.environ['TWILIO_SID'], os.environ['TWILIO_AUTH'])
    client.calls.create(
        twiml=f'<Response><Say>The IPL innings is over. {reason}.</Say></Response>',
        to=os.environ['MY_PHONE'],
        from_=os.environ['TWILIO_FROM']
    )
    # Write the inning name to the file (the sticky note)
    with open(FILE_NAME, "w") as f:
        f.write(inning_name)
    print(f"Call Alert Sent for: {inning_name}")

def check_score():
    url = f"https://cricapi.com{os.environ['CRICKET_API_KEY']}&offset=0"
    try:
        response = requests.get(url).json()
        matches = [m for m in response.get('data', []) if 'IPL' in m.get('name', '')]
        
        if not matches:
            print("No live IPL match.")
            return

        match = matches[0]
        scores = match.get('score', [])
        
        if scores:
            current = scores[-1]
            overs = float(current.get('o', 0))
            wickets = int(current.get('w', 0))
            inning_name = current.get('inning', 'Unknown')

            # Read the 'sticky note'
            last_alerted = ""
            if os.path.exists(FILE_NAME):
                with open(FILE_NAME, "r") as f:
                    last_alerted = f.read().strip()

            # Condition: Is it over AND is it a new event?
            if (overs >= 20.0 or wickets >= 10) and (inning_name != last_alerted):
                trigger_call(f"{overs} overs or {wickets} wickets down", inning_name)
            else:
                print(f"Match status: {inning_name} at {overs} overs. No new alert.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_score()
