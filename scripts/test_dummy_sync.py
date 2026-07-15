import pandas as pd
import os
from datetime import datetime, date
import random

EXCEL_PATH = "movimientos_sabadell.xlsx"

if os.path.exists(EXCEL_PATH):
    df_existente = pd.read_excel(EXCEL_PATH)
else:
    df_existente = pd.DataFrame()

nueva_fila = {
    "referencia_unica": f"DUMMY_{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "fecha": date.today().isoformat(),
    "importe": round(random.uniform(5, 200), 2),
    "moneda": "EUR",
    "tipo": random.choice(["Entrada", "Salida"]),
    "contraparte": "PRUEBA DUMMY SL",
    "iban_contraparte": "ES0000000000000000000000",
    "concepto_banco": "TRANSFERENCIA PRUEBA",
    "concepto_detallado": "Movimiento de prueba (dummy)",
    "categoria": "Prueba",
    "referencia": "TEST-001",
}

df_final = pd.concat([df_existente, pd.DataFrame([nueva_fila])], ignore_index=True)
df_final.to_excel(EXCEL_PATH, index=False)
print(f"Fila dummy añadida. Total filas ahora: {len(df_final)}")