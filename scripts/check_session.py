import jwt as pyjwt
import requests
from datetime import datetime
from pprint import pprint

APPLICATION_ID = "82664702-7eca-48af-be56-fb7b69dea089"
PRIVATE_KEY_PATH = "C:/Users/AryanHareshNarwaniDa/private_prod.key"
SESSION_ID = "cc049060-cea5-41cd-aecd-1f6fea96b2fe"

private_key = open(PRIVATE_KEY_PATH, "rb").read()

iat = int(datetime.now().timestamp())
jwt_body = {
    "iss": "enablebanking.com",
    "aud": "api.enablebanking.com",
    "iat": iat,
    "exp": iat + 3600,
}

jwt_token = pyjwt.encode(
    jwt_body,
    private_key,
    algorithm="RS256",
    headers={"kid": APPLICATION_ID},
)

base_headers = {"Authorization": f"Bearer {jwt_token}"}

r = requests.get(
    f"https://api.enablebanking.com/sessions/{SESSION_ID}",
    headers=base_headers,
)

if r.status_code == 200:
    session = r.json()
    accounts = session.get("accounts", [])
    print(f"Session status: {r.status_code}")
    print(f"Tipo de dato de 'accounts': {type(accounts)}")
    print(f"\nContenido de 'accounts':")
    pprint(accounts)
else:
    print(f"Error {r.status_code}:", r.text)