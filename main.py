from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from models import Base, Book, Review
from database import engine, get_db
from pydantic import BaseModel
import uvicorn
#without llm

app = FastAPI()

class BookCreate(BaseModel):
    title: str
    author: str
    genre: str
    year_published: int
    summary: str

class ReviewCreate(BaseModel):
    user_id: int
    review_text: str
    rating: float

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/books")
async def create_book(book: BookCreate, db: AsyncSession = Depends(get_db)):
    new_book = Book(**book.dict())
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book

@app.get("/books")
async def get_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book))
    return result.scalars().all()

@app.get("/books/{id}")
async def get_book(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).filter(Book.id == id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{id}")
async def update_book(id: int, book: BookCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).filter(Book.id == id))
    db_book = result.scalar_one_or_none()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.dict().items():
        setattr(db_book, key, value)
    await db.commit()
    await db.refresh(db_book)
    return db_book

@app.delete("/books/{id}")
async def delete_book(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).filter(Book.id == id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(book)
    await db.commit()
    return {"detail": "Book deleted"}

@app.post("/books/{id}/reviews")
async def add_review(id: int, review: ReviewCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).filter(Book.id == id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    new_review = Review(**review.dict(), book_id=id)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review

@app.get("/books/{id}/reviews")
async def get_reviews(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).filter(Review.book_id == id))
    return result.scalars().all()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
