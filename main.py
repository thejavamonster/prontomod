import websockets
import asyncio
import json
import requests
import sys
import uuid
import re
from datetime import datetime, timezone
import time

# API Base URL and Credentials
api_base_url = "https://stanfordohs.pronto.io/"
accesstoken = ""
user_id = ""
int_user_id = 

BUBBLE_IDS = [
   
    
]

main_bubble_ID = ""
log_channel_ID = ""
global media
media = []
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {accesstoken}",
}
settings = [1, 1, 1, 1, 1]  # [bad_words, logging, repeat_check, length_check, spam_check]
flagsetting = 3
spam_threshold = 5  # messages per time window
spam_time_window = 10  # seconds
stored_messages = {}
user_message_times = {}  # Track message timestamps per user per bubble
chat_names = {}  # Cache for chat names
warning_message = ""
log_message = ""
last_message_id = ""

# Bad Words List URL
URL = "https://raw.githubusercontent.com/MrSpots1/MrSpots1.github.io/main/words%20%5BMConverter.eu%5D.txt"

# Download Bad Words List
def download_wordlist(url):
    response = requests.get(url)
    if response.status_code == 200:
        words = response.text.split("\n")
        return set(word.strip().lower() for word in words if word.strip())
    else:
        print("Failed to download word list.")
        return set()

BAD_WORDS = download_wordlist(URL)
BAD_WORDS_REGEX = re.compile(r"\b(" + "|".join(re.escape(word) for word in BAD_WORDS) + r")\b", re.IGNORECASE)

def get_channel_code(bubble_id, user_id):
    """Fetch channel code for websocket connection."""
    url = f"{api_base_url}api/clients/chats/{bubble_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data['data'].get('channel_code')

def get_chat_name(bubble_id):
    """Fetch chat name and cache it."""
    if bubble_id in chat_names:
        return chat_names[bubble_id]
    
    try:
        url = f"{api_base_url}api/clients/chats/{bubble_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        chat_name = data['data'].get('title', f'Chat {bubble_id}')
        chat_names[bubble_id] = chat_name
        return chat_name
    except:
        return f'Chat {bubble_id}'

# Function to fetch bubble info
def bubble_info(bubble_id, info='channelid'):
    if bubble_id != 3640189:
        if info == 'channelid':
            return get_channel_code(bubble_id, user_id)
        else:
            url = f"{api_base_url}api/clients/chats/{bubble_id}/memberships/{user_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get(info)
    else:
        return 'skip'

def get_bubble_sid(bubble_id):
    """Fetch the bubble_sid for a given bubble_id using bubble_info."""
    try:
        bubble_sid = bubble_info(int(bubble_id), 'channelid')
        if bubble_sid and bubble_sid != 'skip':
            print(f"Fetched bubble_sid for {bubble_id}: {bubble_sid}")
            return bubble_sid
        else:
            print(f"No bubble_sid found for bubble_id: {bubble_id}")
            return None
    except Exception as e:
        print(f"Error fetching bubble_sid for {bubble_id}: {e}")
        return None

# WebSocket and API Functions
def chat_auth(bubble_id, bubble_sid, socket_id):
    url = f"{api_base_url}api/v1/pusher.auth"
    data = {
        "socket_id": socket_id,
        "channel_name": f"private-bubble.{bubble_id}.{bubble_sid}"
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    bubble_auth = response.json().get("auth")
    print("Bubble Connection Established.")
    return bubble_auth

async def connect_and_listen(bubble_id, bubble_sid):
    uri = "wss://ws-mt1.pusher.com/app/f44139496d9b75f37d27?protocol=7&client=js&version=8.3.0&flash=false"
    try:
        async with websockets.connect(uri) as websocket:
            response = await websocket.recv()
            chat_name = get_chat_name(bubble_id)
            print(f"[{chat_name}] Connected")

            data = json.loads(response)
            if "data" in data:
                inner_data = json.loads(data["data"])
                socket_id = inner_data.get("socket_id", None)

                data = {
                    "event": "pusher:subscribe",
                    "data": {
                        "channel": f"private-bubble.{bubble_id}.{bubble_sid}",
                        "auth": chat_auth(bubble_id, bubble_sid, socket_id)
                    }
                }
                await websocket.send(json.dumps(data))
                
                
                if bubble_id not in stored_messages:
                    stored_messages[bubble_id] = []

            
            async for message in websocket:
                if message == "ping":
                    await websocket.send("pong")
                else:
                    msg_data = json.loads(message)
                    event_name = msg_data.get("event", "")
                    if event_name == "App\\Events\\MessageAdded":
                        msg_content = json.loads(msg_data.get("data", "{}"))
                        msg_text = msg_content.get("message", {}).get("message", "")
                        msg_user = msg_content.get("message", {}).get("user", {})
                        user_firstname = msg_user.get("firstname", "Unknown")
                        user_lastname = msg_user.get("lastname", "User")
                        timestamp = msg_content.get("message", {}).get("created_at", "Unknown timestamp")
                        msg_media = msg_content.get("message", {}).get("messagemedia", [])

                        process_message(msg_text, user_firstname, user_lastname, timestamp, msg_media, bubble_id)
    except Exception as e:
        chat_name = get_chat_name(bubble_id)
        print(f"Error in {chat_name}: {e}")

async def main():
    tasks = []
    
    for bubble_id in BUBBLE_IDS:
        try:
            bubble_sid = get_channel_code(bubble_id, user_id)
            if bubble_sid:
                chat_name = get_chat_name(bubble_id)
                print(f"Starting moderation for {chat_name} ({bubble_id})")
                task = asyncio.create_task(connect_and_listen(bubble_id, bubble_sid))
                tasks.append(task)
            else:
                print(f"Failed to get channel code for bubble {bubble_id}")
        except Exception as e:
            print(f"Error setting up bubble {bubble_id}: {e}")
    
    if tasks:
        print(f"Monitoring {len(tasks)} chat(s)...")
        await asyncio.gather(*tasks)
    else:
        print("No valid bubbles to monitor")

# Mod Bot Logic for Processing Messages
def process_message(msg_text, user_firstname, user_lastname, timestamp, msg_media, bubble_id):
    msg_text_lower = msg_text.lower()
    msg_id = str(uuid.uuid4())  # Simulate unique message ID
    sent_user_id = user_id  # This would be the actual user ID for the message sender

    count = 0
    # Bad Word Check
    if settings[0] == 1:
        count = check_bad_words(msg_text_lower, sent_user_id, bubble_id)
    
    # Logging
    if settings[1] == 1:
        log(msg_text, sent_user_id, msg_media, bubble_id)

    # Repeat Check
    if settings[2] == 1:
        repeat_check(msg_text_lower, sent_user_id, count, bubble_id)
    
    # Message Length Check
    if settings[3] == 1:
        check_length(msg_text_lower, sent_user_id, bubble_id)
    
    # Spam Check
    if settings[4] == 1:
        check_spam(sent_user_id, bubble_id)

def check_bad_words(msg_text, sent_user_id, bubble_id):
    """Check if the message contains any flagged words."""
    if bool(BAD_WORDS_REGEX.search(msg_text)):
        countflags = BAD_WORDS_REGEX.findall(msg_text)
        warning_message = f"Warning: <@{sent_user_id}> sent a flagged message with {len(countflags)} flagged section(s)!"
        chat_name = get_chat_name(bubble_id)
        print(f"[{chat_name}] {warning_message}")
        send_message(warning_message, bubble_id, media)
        return len(countflags)
    return 0

def log(msg_text, sent_user_id, msg_media, bubble_id):
    """Log message details to another channel."""
    chat_name = get_chat_name(bubble_id)
    log_message = f"[{chat_name}] Message sent by <@{sent_user_id}>: {msg_text}"
    send_message(log_message, log_channel_ID, msg_media)
    print(log_message)

def check_length(msg_text, sent_user_id, bubble_id):
    """Check if the message exceeds a set length."""
    if len(msg_text) > 750:
        warning_message = f"Warning: <@{sent_user_id}> sent a message that is {len(msg_text)} characters long!"
        send_message(warning_message, bubble_id, media)
        chat_name = get_chat_name(bubble_id)
        print(f"[{chat_name}] {warning_message}")

def repeat_check(msg_text, sent_user_id, flagcount, bubble_id):
    """Check if the user is repeating a message."""
    if bubble_id not in stored_messages:
        stored_messages[bubble_id] = []
    
    matches = list(filter(lambda row: row[0] == sent_user_id, stored_messages[bubble_id]))
    if matches:
        index = stored_messages[bubble_id].index(matches[0])
        stored_messages[bubble_id][index][1] = stored_messages[bubble_id][index][3]
        stored_messages[bubble_id][index][2] = stored_messages[bubble_id][index][4]
        stored_messages[bubble_id][index][3] = stored_messages[bubble_id][index][5]
        stored_messages[bubble_id][index][4] = stored_messages[bubble_id][index][6]
        stored_messages[bubble_id][index][5] = msg_text
        stored_messages[bubble_id][index][6] = flagcount
        if stored_messages[bubble_id][index][1] == stored_messages[bubble_id][index][3] and stored_messages[bubble_id][index][3] == stored_messages[bubble_id][index][5]:
            warning_message = f"Warning: <@{sent_user_id}> sent a repeated message!"
            send_message(warning_message, bubble_id, media)
        if settings[0] == 1 and flagsetting > 1:
            totalcount = stored_messages[bubble_id][index][6] + stored_messages[bubble_id][index][4] + stored_messages[bubble_id][index][2]
            if totalcount >= flagsetting:
                warning_message = f"Warning: <@{sent_user_id}> has had {totalcount} flagged sections in the last 3 messages!"
                send_message(warning_message, bubble_id, media)
                stored_messages[bubble_id][index][6] = 0
                stored_messages[bubble_id][index][4] = 0
                stored_messages[bubble_id][index][2] = 0
    else:
        stored_messages[bubble_id].append([sent_user_id, "", 0, "", 0, msg_text, flagcount])

def check_spam(sent_user_id, bubble_id):
    """Check if user is sending messages too quickly (spam)."""
    current_time = time.time()
    
    # Initialize tracking for this bubble if needed
    if bubble_id not in user_message_times:
        user_message_times[bubble_id] = {}
    
    # Initialize tracking for this user in this bubble if needed
    if sent_user_id not in user_message_times[bubble_id]:
        user_message_times[bubble_id][sent_user_id] = []
    
    # Add current message time
    user_message_times[bubble_id][sent_user_id].append(current_time)
    
    # Remove messages older than the time window
    user_message_times[bubble_id][sent_user_id] = [
        msg_time for msg_time in user_message_times[bubble_id][sent_user_id]
        if current_time - msg_time <= spam_time_window
    ]
    
    # Check if user exceeded spam threshold
    message_count = len(user_message_times[bubble_id][sent_user_id])
    if message_count >= spam_threshold:
        warning_message = f"Warning: <@{sent_user_id}> is spamming! {message_count} messages in {spam_time_window} seconds!"
        chat_name = get_chat_name(bubble_id)
        print(f"[{chat_name}] {warning_message}")
        send_message(warning_message, bubble_id, media)
        # Reset counter after warning
        user_message_times[bubble_id][sent_user_id] = []

def send_message(message, bubble, send_media):
    """Send a message to the API."""
    unique_uuid = str(uuid.uuid4())
    messageCreatedat = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "id": "Null",
        "uuid": unique_uuid,
        "bubble_id": bubble,
        "message": message,
        "created_at": messageCreatedat,
        "user_id": user_id,
        "messagemedia": send_media
    }
    url = f"{api_base_url}api/v1/message.create"
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

# Start WebSocket Listening
if __name__ == "__main__":
    asyncio.run(main())
