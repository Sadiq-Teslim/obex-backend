from app.core.settings import settings
import httpx


async def send_sms(phone_number: str, message: str) -> bool:
    """
    Sends an SMS using the Termii API.
    """

    url = f"{settings.termii_base_url}/api/sms/send"
    # Format phone number: remove leading 0 if present, then add +234
    if phone_number.startswith("+234"):
        formatted_number = phone_number
    else:
        formatted_number = f"+234{phone_number.lstrip('0')}"
    
    payload = {
        "to": formatted_number,
        "from": settings.termii_sender_id,
        "sms": message,
        "type": "plain",
        "channel": "generic",
        "api_key": settings.termii_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)

        response_data = response.json()

        if response.status_code == 200 and response_data.get("status") == "success":
            print(f"SMS sent successfully to {phone_number}")
            return True
        else:
            print(f"Failed to send SMS: {response_data}")
            return False

    except httpx.HTTPError as e:
        print(f"HTTP error sending SMS: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error sending SMS: {e}")
        return False
