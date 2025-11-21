import uuid
import hmac
import hashlib
from datetime import datetime, timezone

import requests
from django.conf import settings


def send_sms(to: str, text: str) -> dict:
    """
    Solapi sendManyDetail API를 호출하여 SMS를 발송합니다.

    :param to: 수신자 전화번호 (예: '01012345678')
    :param text: 발송할 문자 내용
    :return: API 호출 결과 JSON
    """

    # 1) 인증 정보 준비
    api_key = settings.SOLAPI_API_KEY
    api_secret = settings.SOLAPI_API_SECRET
    sender = settings.SOLAPI_SENDER  # 콘솔에 등록된 발신번호

    # 2) Authorization 헤더용 날짜, salt, signature 생성
    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    salt = uuid.uuid4().hex
    # signature = HMAC-SHA256(date + salt, api_secret)
    message = date + salt
    signature = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    auth_header = (
        f"HMAC-SHA256 apiKey={api_key}, date={date}, "
        f"salt={salt}, signature={signature}"
    )
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": auth_header,
    }

    # 3) API 요청 바디 구성
    url = "https://api.solapi.com/messages/v4/send-many/detail"
    payload = {
        "messages": [
            {
                "to": to,
                "from": sender,
                "text": text
            }
        ]
    }

    # 4) POST 요청 및 결과 반환
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
