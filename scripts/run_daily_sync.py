import jwt as pyjwt
import requests
import pandas as pd
from datetime import datetime, date, timedelta
import os
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ============ CONFIGURACIÓN ============
APPLICATION_ID = "82664702-7eca-48af-be56-fb7b69dea089"
PRIVATE_KEY_PATH = "C:/Users/AryanHareshNarwaniDa/private_prod.key"
SESSION_ID = "cc049060-cea5-41cd-aecd-1f6fea96b2fe"
ACCOUNT_UID = "63d97c75-9cff-476c-b4a1-23f9b2294aeb"
EXCEL_PATH = "movimientos_sabadell.xlsx"
REGLAS_PATH = "reglas_conceptos.xlsx"
LOG_PATH = "sync_log.txt"
DIAS_AVISO_EXPIRACION = 10  # avisa si el consentimiento caduca en menos de X días
# ========================================

def log(mensaje):
    linea = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}"
    print(linea)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

def generar_jwt():
    private_key = open(PRIVATE_KEY_PATH, "rb").read()
    iat = int(datetime.now().timestamp())
    jwt_body = {"iss": "enablebanking.com", "aud": "api.enablebanking.com", "iat": iat, "exp": iat + 3600}
    return pyjwt.encode(jwt_body, private_key, algorithm="RS256", headers={"kid": APPLICATION_ID})

def main():
    log("=== Iniciando sincronización diaria ===")
    headers = {"Authorization": f"Bearer {generar_jwt()}"}

    # 1. Comprobar que la sesión sigue viva y avisar si el consentimiento va a caducar
    r = requests.get(f"https://api.enablebanking.com/sessions/{SESSION_ID}", headers=headers)
    if r.status_code != 200:
        log(f"❌ ERROR comprobando sesión: {r.status_code} {r.text}")
        log("   El consentimiento probablemente ha expirado. Hay que rehacer start_auth_prod.py.")
        return

    valid_until_str = r.json().get("access", {}).get("valid_until")
    if valid_until_str:
        valid_until = datetime.fromisoformat(valid_until_str.replace("Z", "+00:00"))
        dias_restantes = (valid_until - datetime.now(valid_until.tzinfo)).days
        if dias_restantes <= DIAS_AVISO_EXPIRACION:
            log(f"⚠️  AVISO: el consentimiento caduca en {dias_restantes} días. Hay que renovarlo pronto.")
        else:
            log(f"Consentimiento OK, caduca en {dias_restantes} días.")

    # 2. Cargar lo que ya tenemos guardado
    if os.path.exists(EXCEL_PATH):
        df_existente = pd.read_excel(EXCEL_PATH)
        referencias_existentes = set(df_existente["referencia_unica"].astype(str)) if "referencia_unica" in df_existente.columns else set()
    else:
        df_existente = pd.DataFrame()
        referencias_existentes = set()

    # 3. Traer movimientos del banco
    r = requests.get(
        f"https://api.enablebanking.com/accounts/{ACCOUNT_UID}/transactions",
        headers=headers,
        params={"date_from": (date.today() - timedelta(days=89)).isoformat(), "date_to": date.today().isoformat()},
    )
    if r.status_code == 429:
        log("⚠️  Límite de consultas diarias alcanzado (429). Se reintentará mañana.")
        return
    if r.status_code != 200:
        log(f"❌ ERROR trayendo movimientos: {r.status_code} {r.text}")
        return

    transacciones = r.json().get("transactions", [])
    nuevas = []
    for t in transacciones:
        ref_unica = f"{t.get('entry_reference')}_{t.get('booking_date')}_{t['transaction_amount']['amount']}"
        if ref_unica not in referencias_existentes:
            nuevas.append({
                "referencia_unica": ref_unica,
                "fecha": t.get("booking_date"),
                "importe": t["transaction_amount"]["amount"],
                "moneda": t["transaction_amount"]["currency"],
                "tipo": "Entrada" if t.get("credit_debit_indicator") == "CRDT" else "Salida",
                "contraparte": (t.get("creditor") or {}).get("name") or (t.get("debtor") or {}).get("name"),
                "iban_contraparte": ((t.get("creditor_account") or {}).get("iban") or (t.get("debtor_account") or {}).get("iban")),
                "concepto_banco": " | ".join(t.get("remittance_information") or []),
                "concepto_detallado": "",
                "referencia": t.get("reference_number"),
            })

    log(f"Movimientos en el banco (89 días): {len(transacciones)} | Nuevos: {len(nuevas)}")

    if not nuevas:
        log("Sin novedades. Fin.")
        return

    df_final = pd.concat([df_existente, pd.DataFrame(nuevas)], ignore_index=True)

    # 4. Aplicar el motor de reglas
    reglas = pd.read_excel(REGLAS_PATH, sheet_name="reglas")

    def buscar_concepto_y_categoria(row):
        if row.get("concepto_detallado") and row["concepto_detallado"] != "⚠️ REVISAR":
            return row["concepto_detallado"], row.get("categoria", "")

        iban = str(row.get("iban_contraparte") or "")
        importe = f"{float(row['importe']):.2f}"
        texto = f"{row.get('contraparte') or ''} {row.get('concepto_banco') or ''}".upper()

        for _, rg in reglas[reglas["tipo_regla"] == "iban_importe"].iterrows():
            try:
                iban_r, importe_r = rg["criterio"].split("|")
            except ValueError:
                continue
            if iban == iban_r.strip() and importe == f"{float(importe_r):.2f}":
                return rg["concepto_detallado"], rg.get("categoria", "Sin categoria")

        for _, rg in reglas[reglas["tipo_regla"] == "iban"].iterrows():
            if iban == str(rg["criterio"]).strip():
                return rg["concepto_detallado"], rg.get("categoria", "Sin categoria")

        for _, rg in reglas[reglas["tipo_regla"] == "texto_contiene"].iterrows():
            if str(rg["criterio"]).upper() in texto:
                return rg["concepto_detallado"], rg.get("categoria", "Sin categoria")

        return "⚠️ REVISAR", "Sin categoria"

    resultados = df_final.apply(buscar_concepto_y_categoria, axis=1)
    df_final["concepto_detallado"] = [r[0] for r in resultados]
    df_final["categoria"] = [r[1] for r in resultados]


    revisar = (df_final["concepto_detallado"] == "⚠️ REVISAR").sum()
    log(f"✅ Excel actualizado. {len(nuevas)} nuevos añadidos. {revisar} pendientes de revisión en total.")
    log("=== Fin ===\n")

if __name__ == "__main__":
    main()