import os

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="GlobalShop API", version="1.0.0")

DATABASES = {
    1: {"host": os.getenv("NODE1_HOST", "node1")},
    2: {"host": os.getenv("NODE2_HOST", "node2")},
    3: {"host": os.getenv("NODE3_HOST", "node3")},
    0: {"host": os.getenv("NODE4_HOST", "node4")},
}


def get_connection(product_id: int):
    config = DATABASES[product_id % 4]
    return psycopg2.connect(
        host=config["host"],
        port=5432,
        dbname="globalshop",
        user="globalshop",
        password="globalshop123",
        connect_timeout=3,
    )


class PurchaseRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)


@app.get("/")
def home():
    return {"message": "GlobalShop API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/produits/{product_id}")
def get_product(product_id: int):
    if product_id <= 0:
        raise HTTPException(400, "ID produit invalide")

    # Essayer d'abord le nœud propriétaire, puis les autres.
    owner = product_id % 4
    node_order = [owner, 1, 2, 3, 0]
    node_order = list(dict.fromkeys(node_order))

    last_error = None

    for node in node_order:
        try:
            config = DATABASES[node]

            with psycopg2.connect(
                host=config["host"],
                port=5432,
                dbname="globalshop",
                user="globalshop",
                password="globalshop123",
                connect_timeout=2,
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT product_id, nom, prix, stock
                        FROM produit
                        WHERE product_id = %s
                        """,
                        (product_id,),
                    )
                    row = cur.fetchone()

            if row is not None:
                return {
                    "product_id": row[0],
                    "nom": row[1],
                    "prix": float(row[2]),
                    "stock": row[3],
                    "served_by": config["host"],
                    "fallback": node != owner,
                }

        except psycopg2.Error as exc:
            last_error = exc

    if last_error is not None:
        raise HTTPException(
            status_code=503,
            detail="Aucun nœud accessible pour lire ce produit",
        ) from last_error

    raise HTTPException(404, "Produit introuvable sur les nœuds accessibles")

@app.post("/acheter")
def buy_product(request: PurchaseRequest):
    try:
        with get_connection(request.product_id) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE produit
                    SET stock = stock - %s
                    WHERE product_id = %s AND stock >= %s
                    RETURNING product_id, nom, stock
                    """,
                    (
                        request.quantity,
                        request.product_id,
                        request.quantity,
                    ),
                )
                row = cur.fetchone()

                if row is None:
                    cur.execute(
                        "SELECT stock FROM produit WHERE product_id = %s",
                        (request.product_id,),
                    )
                    product = cur.fetchone()

                    if product is None:
                        raise HTTPException(404, "Produit introuvable")

                    raise HTTPException(
                        409,
                        detail={
                            "message": "Stock insuffisant",
                            "stock_disponible": product[0],
                        },
                    )

                return {
                    "success": True,
                    "message": "Achat accepté",
                    "product_id": row[0],
                    "nom": row[1],
                    "quantity": request.quantity,
                    "stock_restant": row[2],
                }

    except HTTPException:
        raise
    except psycopg2.Error as exc:
        raise HTTPException(
            503, "Base de données temporairement indisponible"
        ) from exc
