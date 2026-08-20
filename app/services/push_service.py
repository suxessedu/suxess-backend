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
    Sends push notifications to multiple Expo push tokens in batches.
    """
    if not tokens:
        return None
    
    # Filter out invalid tokens (support both ExponentPushToken and ExpoPushToken)
    valid_tokens = [t for t in tokens if t and isinstance(t, str) and ('ExponentPushToken' in t or 'ExpoPushToken' in t)]
    if not valid_tokens:
        return None

    # Expo accepts batches of up to 100 messages at once
    messages = [{
        'to': token,
        'sound': 'default',
        'title': title,
        'body': body,
        'data': data or {},
    } for token in valid_tokens]

    try:
        response = requests.post(
            EXPO_PUSH_API_URL,
            headers={
                'Accept': 'application/json',
                'Accept-encoding': 'gzip, deflate',
                'Content-Type': 'application/json',
            },
            data=json.dumps(messages)
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Log the error but don't crash the app
        print(f"Error sending push notification: {e}")
        return None
