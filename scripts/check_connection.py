import jwt as pyjwt
import requests
from datetime import datetime
from pprint import pprint

APPLICATION_ID = "dab24098-2efd-40f5-b516-70bf71f96fa5"
PRIVATE_KEY_PATH = "C:/Users/AryanHareshNarwaniDa/private.key"

private_key = open(PRIVATE_KEY_PATH, "rb").read()

iat = int(datetime.now().timestamp())
jwt_body = {
    "iss": "enablebanking.com",   # siempre este valor literal
    "aud": "api.enablebanking.com",  # siempre este valor literal
    "iat": iat,
    "exp": iat + 3600,  # token válido 1 hora
}

jwt_token = pyjwt.encode(
    jwt_body,
    private_key,
    algorithm="RS256",
    headers={"kid": APPLICATION_ID},  # el kid es tu application_id
)

base_headers = {"Authorization": f"Bearer {jwt_token}"}

# 1. Comprobar que la app se autentica correctamente
r = requests.get("https://api.enablebanking.com/application", headers=base_headers)
print(f"Status autenticación: {r.status_code}")
pprint(r.json())

# 2. Listar bancos disponibles en España y buscar Sabadell
r = requests.get("https://api.enablebanking.com/aspsps?country=ES", headers=base_headers)
aspsps = r.json()["aspsps"]
sabadell = [b for b in aspsps if "sabadell" in b["name"].lower()]

print("\nBancos con 'Sabadell' en el nombre:")
pprint(sabadell)