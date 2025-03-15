# prontomod
adds modding support to python

#### How it works
This is a very simple program: only 109 lines of Python. Given a chat id, it reads messages from the chat and scans them for profanity or violent language. The filter is taken from Luis von Ahn's research group at Carnegie Mellon University: https://www.cs.cmu.edu/~biglou/. (It's a very complete list- thanks Luis!) It sends a warning message if it detects anything bad, tagging the person who sent the message. If the bot has owner privileges, it could also kick the person from the group after repeated violations. Since we already have the framework of the program set up, it's very easy to add features like kicking users, timing them out, or privately messaging them for more serious violations. All it takes is a simple function call to the API-- the authorization stuff is already set up. We didn't include these things because we don't have access to a user account with owner privileges.

This program was stress-tested by releasing it into a chat full of the most degenerate middle schoolers to walk the planet. It functioned successfully, and sufficiently annoyed the middle schoolers. 


#### How to use
All you have to do to use this is download the main.py file, then replace the access_token and bubble_id variables with your information. Your access token can be found by opening up the Chrome console while in Pronto and capturing a network request while you send a message. Click on the "message.create" request in the left sidebar. Then, go to the "Headers" tab and find the "Bearer" variable, as shown in the picture. That's your access token.

![image](https://github.com/user-attachments/assets/b74d50cb-97c6-442e-9fb2-a27369cf0b66)


The bubble_id is just the identification number for a group chat. This can be found by just looking at the URL for a specific Pronto chat and copying the number:

![image](https://github.com/user-attachments/assets/4c896671-a97d-498a-ac12-bd5c7f6310a9)

That's all you have to do to get this working. The imports are also very straightforward: requests, uuid, datetime, time, json, and re. 
