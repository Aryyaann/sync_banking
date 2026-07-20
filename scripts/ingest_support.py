from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
import uuid
import os
import re
import glob
import argparse

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:TuNuevaContraseñaSegura2026XYZ@kodama.proxy.rlwy.net:50752/railway")
engine = create_engine(DATABASE_URL)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def chunk_markdown(texto, max_chars=800):
    secciones = re.split(r"\n(?=#{1,3} )", texto)
    chunks = []
    for seccion in secciones:
        seccion = seccion.strip()
        if not seccion:
            continue
        if len(seccion) <= max_chars:
            chunks.append(seccion)
        else:
            parrafos = seccion.split("\n\n")
            actual = ""
            for p in parrafos:
                if len(actual) + len(p) > max_chars and actual:
                    chunks.append(actual.strip())
                    actual = p
                else:
                    actual += "\n\n" + p
            if actual.strip():
                chunks.append(actual.strip())
    return chunks


def main(product, path):
    archivos = glob.glob(os.path.join(path, "README.md")) + glob.glob(os.path.join(path, "docs", "*.md"))

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM support_chunks WHERE product = :product"), {"product": product})

        total = 0
        for archivo in archivos:
            with open(archivo, "r", encoding="utf-8") as f:
                contenido = f.read()

            chunks = chunk_markdown(contenido)
            embeddings = model.encode(chunks)

            for chunk_text_val, embedding in zip(chunks, embeddings):
                conn.execute(text("""
                    INSERT INTO support_chunks (id, product, source_file, chunk_text, embedding)
                    VALUES (:id, :product, :source, :chunk, :emb)
                """), {
                    "id": str(uuid.uuid4()),
                    "product": product,
                    "source": os.path.basename(archivo),
                    "chunk": chunk_text_val,
                    "emb": list(map(float, embedding)),
                })
                total += 1

            print(f"  {archivo}: {len(chunks)} fragmentos")

    print(f"\n✅ {total} fragmentos indexados para el producto '{product}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", required=True, help="Nombre del producto, ej. 'sync-banking'")
    parser.add_argument("--path", required=True, help="Ruta a la carpeta raíz del proyecto (donde están README.md y docs/)")
    args = parser.parse_args()
    main(args.product, args.path)