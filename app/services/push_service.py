import requests
import json
from flask import current_app

EXPO_PUSH_API_URL = 'https://exp.host/--/api/v2/push/send'

def send_push_notification(token, title, body, data=None):
    """
    Sends a push notification to a single Expo push token.
    """
    return send_push_notifications([token], title, body, data)

def send_push_notifications(tokens, title, body, data=None):
    """
    Sends push notifications to multiple Expo push tokens.
    """
    if not tokens:
        return
    
    # Filter out invalid tokens (basic check)
    valid_tokens = [t for t in tokens if t and t.startswith('ExponentPushToken')]
    if not valid_tokens:
        return

    message = {
        'to': valid_tokens,
        'sound': 'default',
        'title': title,
        'body': body,
        'data': data or {},
    }

    try:
        response = requests.post(
            EXPO_PUSH_API_URL,
            headers={
                'Accept': 'application/json',
                'Accept-encoding': 'gzip, deflate',
                'Content-Type': 'application/json',
            },
            data=json.dumps(message)
        )
        response.raise_for_status()
        # In a real app, we should check for errors in the response (e.g. invalid tokens)
        # and remove them from the DB.
        return response.json()
    except Exception as e:
        # Log the error but don't crash the app
        print(f"Error sending push notification: {e}")
        return None
