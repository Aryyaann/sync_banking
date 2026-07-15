from fastapi import FastAPI, HTTPException, Header, Query, Response
from sqlalchemy import create_engine, text
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import re
import io
from sync_engine import sync_negocio, DATABASE_URL
import os

app = FastAPI()
# API_TOKEN = "DyWwx4k1dIKHW_7pjk4diIEpHxE6JcTtNjvM_JoWflw"  # el mismo que ya usas
API_TOKEN = os.environ.get("API_TOKEN", "DyWwx4k1dIKHW_7pjk4diIEpHxE6JcTtNjvM_JoWflw")

engine = create_engine(DATABASE_URL)


def check_auth(authorization):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="No autorizado")


@app.get("/status")
def status():
    return {"status": "vivo"}


@app.get("/transactions")
def get_transactions(business_id: str = Query(...), authorization: str = Header(None)):
    check_auth(authorization)
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT fecha, importe, moneda, tipo, contraparte, iban_contraparte,
                   concepto_banco, concepto_detallado, categoria, referencia
            FROM transactions WHERE business_id = :bid ORDER BY fecha DESC
        """), {"bid": business_id}).mappings().all()
    return {"count": len(rows), "transactions": [dict(r) for r in rows]}


@app.post("/sync")
def trigger_sync(business_id: str = Query(...), bank_connection_id: str = Query(...),
                  authorization: str = Header(None)):
    check_auth(authorization)
    resultado = sync_negocio(business_id, bank_connection_id)
    return resultado


@app.get("/transactions/export")
def export_excel(business_id: str = Query(...), authorization: str = Header(None)):
    check_auth(authorization)
    import pandas as pd

    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT fecha, tipo, importe, moneda, contraparte, concepto_detallado,
                   concepto_banco, categoria, iban_contraparte, referencia
            FROM transactions WHERE business_id = :bid ORDER BY fecha
        """), conn, params={"bid": business_id})

    if df.empty:
        raise HTTPException(status_code=404, detail="No hay movimientos para este negocio")

    df["categoria"] = df["categoria"].fillna("Sin categoria")
    COLUMNAS = list(df.columns)

    HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
    HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=11)
    ENTRADA_FILL = PatternFill("solid", fgColor="E2EFDA")
    SALIDA_FILL = PatternFill("solid", fgColor="FCE4EC")
    REVISAR_FILL = PatternFill("solid", fgColor="FFF2CC")
    BORDE = Border(*(Side(style="thin", color="D9D9D9"),) * 4)

    def limpiar_nombre_hoja(nombre):
        return re.sub(r'[\\/*?:\[\]]', '', str(nombre))[:31] or "Sin categoria"

    def escribir_hoja(ws, data):
        ws.append(COLUMNAS)
        for col in range(1, len(COLUMNAS) + 1):
            c = ws.cell(row=1, column=col)
            c.fill, c.font, c.border = HEADER_FILL, HEADER_FONT, BORDE
            c.alignment = Alignment(horizontal="center", vertical="center")

        for _, row in data.iterrows():
            ws.append([row.get(c) for c in COLUMNAS])
            r = ws.max_row
            fill = REVISAR_FILL if row.get("concepto_detallado") == "⚠️ REVISAR" else (
                ENTRADA_FILL if row.get("tipo") == "Entrada" else SALIDA_FILL)
            for col in range(1, len(COLUMNAS) + 1):
                cell = ws.cell(row=r, column=col)
                cell.font = Font(name="Arial", size=10)
                cell.border = BORDE
                cell.fill = fill
                if COLUMNAS[col - 1] == "importe":
                    cell.number_format = '#,##0.00 €;[RED]-#,##0.00 €'

        for col in range(1, len(COLUMNAS) + 1):
            letra = get_column_letter(col)
            max_len = max([len(str(ws.cell(row=r, column=col).value or "")) for r in range(1, ws.max_row + 1)], default=10)
            ws.column_dimensions[letra].width = min(max(max_len + 3, 12), 45)
        ws.freeze_panes = "A2"

    wb = openpyxl.Workbook()
    ws_resumen = wb.active
    ws_resumen.title = "Resumen"
    escribir_hoja(ws_resumen, df)

    for categoria in sorted(df["categoria"].unique()):
        subset = df[df["categoria"] == categoria]
        nombre = limpiar_nombre_hoja(categoria)
        base, i = nombre, 1
        while nombre in wb.sheetnames:
            i += 1
            nombre = f"{base[:28]}_{i}"
        escribir_hoja(wb.create_sheet(nombre), subset)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return Response(
        content=buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reporte.xlsx"},
    )