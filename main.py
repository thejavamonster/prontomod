import requests
import uuid
from datetime import datetime, timezone
import time
import json
import re

accesstoken = "ET8DUU4e3PCeUNtfDHd8wmcZZOM4s6dDWA3aAN6M.1323771141"
api_base_url = "https://stanfordohs.pronto.io/"
user_id = "6056675"
bubbleID = "3832006"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {accesstoken}",
}

warning_message = ""
last_message_id = ""

URL = "https://raw.githubusercontent.com/MrSpots1/MrSpots1.github.io/main/words%20%5BMConverter.eu%5D.txt"

def download_wordlist(url):
    """
    Downloads the bad words list from the given URL.
    
    Args:
    - url (str): The URL of the text file.

    Returns:
    - set: A set of bad words in lowercase.
    """
    response = requests.get(url)
    
    if response.status_code == 200:
        words = response.text.split("\n")  # Split by lines
        # Ensure all words are in lowercase and remove empty lines
        return set(word.strip().lower() for word in words if word.strip())
    else:
        print("Failed to download word list.")
        return set()

def fetch_latest_message():
    """Fetch only the most recent message."""
    url = f"{api_base_url}api/v1/bubble.history"
    data = {"bubble_id": bubbleID}
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        messages = response.json().get("messages", [])
        return messages[0]  # Return the most recent message
    else:
        print(f"HTTP error occurred: {response.status_code} - {response.text}")
    return None

def monitor_messages():
    """Continuously fetch the latest message and check for flagged words."""
    global warning_message  
    global last_message_id
    
    while True:
        msg = fetch_latest_message()

        if msg and isinstance(msg, dict) and "message" in msg and "user_id" in msg and "id" in msg:
            msg_id = msg["id"]
            msg_text = msg["message"].lower()

            if msg_id != last_message_id:  # Only process if it's a new message
                last_message_id = msg_id  # Update last seen message

                # Check the message for flagged words using regex
                if bool(BAD_WORDS_REGEX.search(msg_text)):
                    warning_message = f"Warning: <@{msg['user_id']}> sent a flagged message!"
                    send_message(warning_message)  # Send alert
                    print(warning_message)

        time.sleep(1)  # Poll every 1 second

def send_message(message):
    """Send a message to the API."""
    unique_uuid = str(uuid.uuid4())
    messageCreatedat = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "id": "Null",
        "uuid": unique_uuid,
        "bubble_id": bubbleID,
        "message": message,
        "created_at": messageCreatedat,
        "user_id": user_id,
        "messagemedia": []
    }

    url = f"{api_base_url}api/v1/message.create"
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

BAD_WORDS = download_wordlist(URL)


BAD_WORDS_REGEX = re.compile(r"\b(" + "|".join(re.escape(word) for word in BAD_WORDS) + r")\b", re.IGNORECASE)

# Start monitoring messages
monitor_messages()
