import os
import requests
from twilio.rest import Client

FILE_NAME = "last_alerted_inning.txt"
# Permanent ID for IPL 2026 in CricketData.org
IPL_2026_SERIES_ID = "87c62aac-bc3c-4738-ab93-19da0690488f"

def trigger_call(reason, event_id):
    client = Client(os.environ['TWILIO_SID'], os.environ['TWILIO_AUTH'])
    client.calls.create(
        twiml=f'<Response><Say>IPL Event: {reason}.</Say></Response>',
        to=os.environ['MY_PHONE'],
        from_=os.environ['TWILIO_FROM']
    )
    with open(FILE_NAME, "w") as f:
        f.write(event_id)
    print(f"Call Sent: {event_id} - {reason}")

def check_score():
    # Correct URL structure with F-string
    url = f"https://api.cricapi.com/v1/currentMatches?apikey={os.environ['CRICKET_API_KEY']}&offset=0"
    
    try:
        response = requests.get(url).json()
        all_matches = response.get('data', [])

        # 1. Filter strictly by IPL 2026 Series ID
        ipl_matches = [m for m in all_matches if m.get('series_id') == IPL_2026_SERIES_ID]
        
        # 2. Find the active match (Started but NOT ended)
        target_match = next((m for m in ipl_matches if m.get('matchStarted') and not m.get('matchEnded')), None)
        
        # Fallback to the most recent ended match
        if not target_match:
            target_match = next((m for m in ipl_matches if m.get('matchStarted') and m.get('matchEnded')), None)

        if not target_match:
            print("No active IPL 2026 match found.")
            return

        match_name = target_match.get('name')
        match_ended = target_match.get('matchEnded', False)
        scores = target_match.get('score', [])
        
        # Memory Check
        last_alerted = ""
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, "r") as f:
                last_alerted = f.read().strip()

        match_id = target_match.get('id', 'match')
        
        if match_ended:
            event_id = f"{match_id}-ENDED"
            if event_id != last_alerted:
                trigger_call("The match has officially ended", event_id)
                printf("The match has ended: {match_name}")
        elif scores:
            current_inning = scores[-1]
            inning_name = current_inning.get('inning')
            overs = float(current_inning.get('o', 0))
            wickets = int(current_inning.get('w', 0))
            
            event_id = f"{match_id}-{inning_name}"
            
            # Trigger for 20 overs or all-out (10 wickets)
            if (overs >= 20.0 or wickets >= 10) and (event_id != last_alerted):
                trigger_call(f"{inning_name} complete at {overs} overs", event_id)
            else:
                print(f"Monitoring {match_name}: {inning_name} at {overs} ov.")
                
    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    check_score()
