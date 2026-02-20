from io_db_tools import db_create_category
import json
import asyncio


async def add_categories():
    with open('categories.json', 'r', encoding='utf-8') as f:
        categories = json.load(f)
    for ctg in categories:
        await db_create_category(ctg)


asyncio.run(add_categories())
