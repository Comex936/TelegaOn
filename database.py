import os

import asyncpg


DATABASE_URL = os.getenv("DATABASE_URL")


async def create_pool():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL не настроен в Railway Variables"
        )

    return await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5,
    )


async def init_db(pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                game TEXT DEFAULT '',
                price INTEGER NOT NULL,
                description TEXT DEFAULT '',
                image TEXT DEFAULT '',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Если таблица была создана раньше
        # без поля game — добавляем его.
        await conn.execute(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS game TEXT DEFAULT ''
            """
        )


async def get_products(pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id,
                name,
                category,
                game,
                price,
                description,
                image,
                is_active
            FROM products
            WHERE is_active = TRUE
            ORDER BY id DESC
            """
        )

        return [dict(row) for row in rows]


async def add_product(
    pool,
    name,
    category,
    game,
    price,
    description="",
    image="",
):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO products (
                name,
                category,
                game,
                price,
                description,
                image
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            name,
            category,
            game,
            price,
            description,
            image,
        )

        return row["id"]


async def delete_product(pool, product_id):
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE products
            SET is_active = FALSE
            WHERE id = $1
            """,
            product_id,
        )

        return result
