# Import Library
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from chatbot import run_manual, run_chatbot

app = FastAPI()

@app.get('/')
def index():
    return {'message': 'Ecommerce Product Recommendation with ChatGPT'}

class Item(BaseModel):
    department: str
    category: str
    brand: str
    price: str
    top_k: int = 5
    min_rating: float = 0.0
    language: str = "English"

@app.post("/manual")
async def manual(item: Item):
    answer, metadata = run_manual(
        department=item.department,
        category=item.category,
        brand=item.brand,
        price=item.price,
        top_k=item.top_k,
        min_rating=item.min_rating,
        language=item.language
    )
    return {"answer": answer, "products": metadata}

class Query(BaseModel):
    query: str
    top_k: int = 5
    min_rating: float = 0.0
    language: str = "English"

@app.post("/chatbot")
async def get_answer(query: Query):
    answer, metadata = run_chatbot(
        query = query.query,
        top_k = query.top_k,
        min_rating = query.min_rating,
        language = query.language
    )
    return {"answer": answer, "products": metadata}

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)