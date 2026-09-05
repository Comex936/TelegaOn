import o

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import (
    create_pool,
    init_db,
    get_products,
    add_product,
    delete_product,
)


app = FastAPI(title="Game Market API")


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://comex936.github.io",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# DATABASE
# =========================

pool = None


@app.on_event("startup")
async def startup():
    global pool

    pool = await create_pool()
    await init_db(pool)


@app.on_event("shutdown")
async def shutdown():
    global pool

    if pool:
        await pool.close()


# =========================
# HOME
# =========================

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Game Market API работает",
    }


# =========================
# PRODUCTS
# =========================

@app.get("/api/products")
async def products():
    if pool is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not ready",
        )

    return await get_products(pool)
