import requests
import uuid
from datetime import datetime, timezone
import time
import json
import re 

accesstoken = "" #ENTER YOUR PRONTO ACCESS TOKEN HERE
api_base_url = "https://stanfordohs.pronto.io/"
user_id = "" #ENTER YOUR USER ID HERE
bubbleID = "" #ENTER THE GROUP ID HERE!


headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {accesstoken}",
}


warning_message = ""
last_message_id = ""

URL = "https://www.cs.cmu.edu/~biglou/resources/bad-words.txt"

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
        words = response.text.split("\n") 
        return set(word.strip().lower() for word in words if word.strip())  
    else:
        print("Failed to download word list.")
        return set()

        

def fetch_latest_message():
    """Fetch only the most recent message"""
    url = f"{api_base_url}api/v1/bubble.history"
    data = {"bubble_id": bubbleID}
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        messages = response.json().get("messages", [])
        return messages[0]  
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

            if msg_id != last_message_id:  #only process if it's a new message
                last_message_id = msg_id  #update last seen message

                words = msg_text.lower()
                if bool(BAD_WORDS_REGEX.search(msg_text)):
                    warning_message = f"Warning: <@{msg['user_id']}> sent a flagged message!"
                    send_message(warning_message)  #Send alert
                    print(warning_message)  

        time.sleep(1)  #can change if necessary



def send_message(message):
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

monitor_messages()
