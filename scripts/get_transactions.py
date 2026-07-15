import jwt as pyjwt
import requests
from datetime import datetime
from pprint import pprint
from datetime import date
from datetime import datetime, timezone, timedelta
import pandas as pd

APPLICATION_ID = "82664702-7eca-48af-be56-fb7b69dea089"
PRIVATE_KEY_PATH = "C:/Users/AryanHareshNarwaniDa/private_prod.key"
ACCOUNT_UID = "63d97c75-9cff-476c-b4a1-23f9b2294aeb"

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
    f"https://api.enablebanking.com/accounts/{ACCOUNT_UID}/transactions",
    headers=base_headers,
    params={
        "date_from": (date.today() - timedelta(days=89)).isoformat(),
        "date_to": date.today().isoformat(),
    },
)

if r.status_code == 200:
    data = r.json()
    transactions = data.get("transactions", [])
    print(f"Total movimientos: {len(transactions)}")

    rows = []
    for t in transactions:
        rows.append({
            "fecha": t.get("booking_date"),
            "importe": t["transaction_amount"]["amount"],
            "moneda": t["transaction_amount"]["currency"],
            "tipo": "Entrada" if t.get("credit_debit_indicator") == "CRDT" else "Salida",
            "contraparte": (t.get("creditor") or {}).get("name") or (t.get("debtor") or {}).get("name"),
            "iban_contraparte": ((t.get("creditor_account") or {}).get("iban")
                                  or (t.get("debtor_account") or {}).get("iban")),
            "concepto_banco": " | ".join(t.get("remittance_information") or []),
            "referencia": t.get("reference_number"),
        })

    df = pd.DataFrame(rows)
    pd.set_option("display.max_colwidth", 40)
    pd.set_option("display.width", 200)
    print("\n" + df.to_string(index=False))

    # Bonus: lo exporta ya a un Excel de verdad
    df.to_excel("movimientos_sabadell.xlsx", index=False)
    print("\n✅ Guardado también en movimientos_sabadell.xlsx")
else:
    print(f"Error {r.status_code}:", r.text)