import pandas as pd
import re

MOVIMIENTOS_PATH = "movimientos_sabadell.xlsx"
REGLAS_PATH = "reglas_conceptos.xlsx"

df = pd.read_excel(MOVIMIENTOS_PATH)
reglas = pd.read_excel(REGLAS_PATH, sheet_name="reglas")

def buscar_concepto(row):
    iban = str(row.get("iban_contraparte") or "")
    importe = f"{float(row['importe']):.2f}"
    texto_busqueda = f"{row.get('contraparte') or ''} {row.get('concepto_banco') or ''}".upper()

    # 1. Prioridad más alta: iban + importe exacto
    for _, r in reglas[reglas["tipo_regla"] == "iban_importe"].iterrows():
        try:
            iban_regla, importe_regla = r["criterio"].split("|")
        except ValueError:
            continue
        if iban == iban_regla.strip() and importe == f"{float(importe_regla):.2f}":
            return r["concepto_detallado"]

    # 2. Coincidencia por IBAN solo
    for _, r in reglas[reglas["tipo_regla"] == "iban"].iterrows():
        if iban == str(r["criterio"]).strip():
            return r["concepto_detallado"]

    # 3. Coincidencia por texto contenido
    for _, r in reglas[reglas["tipo_regla"] == "texto_contiene"].iterrows():
        if str(r["criterio"]).upper() in texto_busqueda:
            return r["concepto_detallado"]

    return "⚠️ REVISAR"

df["concepto_detallado"] = df.apply(buscar_concepto, axis=1)

sin_revisar = (df["concepto_detallado"] != "⚠️ REVISAR").sum()
por_revisar = (df["concepto_detallado"] == "⚠️ REVISAR").sum()

df.to_excel(MOVIMIENTOS_PATH, index=False)

print(f"✅ {sin_revisar} movimientos enriquecidos automáticamente")
print(f"⚠️  {por_revisar} movimientos sin regla — necesitan revisión manual")