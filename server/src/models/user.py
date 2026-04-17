from datetime import datetime

"""
This for structuring the received data from user 
"""

def create_user(email:str, hash_password:str) -> dict:
    return {
        "email": email,
        "hash_password": hash_password,
        "profile":{
            "age": None,  # User age
            "gender": None,  # User gender
            "occupation": None,  # User occupation
            "sleep_hours": None,  # Sleep pattern
            "social_support": None,  # Support level
            "life_events": []  # List of major life events
        },
        "created_at": datetime.now().isoformat(),
        # Tokens (for refresh token storage)
        "refresh_tokens": []  # Store active refresh tokens
    }