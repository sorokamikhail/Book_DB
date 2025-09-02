from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from typing import List, Optional, Callable
from pydantic import BaseModel
from functools import partial
Base = declarative_base()
DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app = FastAPI()
class BookDB(Base):   
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    description = Column(String, nullable=True)
Base.metadata.create_all(bind=engine)
class BookCreate(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    description: Optional[str] = None
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def create_book_in_db(db: Session, book_data: BookCreate):
    db_book = BookDB(**book_data.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book
def get_all_books_from_db(db: Session) -> List[BookDB]:
    return db.query(BookDB).all()
def get_book_by_id_from_db(db: Session, book_id: int) -> Optional[BookDB]:
    return db.query(BookDB).filter(BookDB.id == book_id).first()
def update_book_in_db(db: Session, db_book: BookDB, book_data: BookUpdate):
    update_data = book_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    db.commit()
    db.refresh(db_book)
    return db_book
def delete_book_from_db(db: Session, db_book: BookDB) -> None:
    db.delete(db_book)
    db.commit()
def validate_book_exists(book_id: int, db: Session = Depends(get_db)):
    book = get_book_by_id_from_db(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
@app.post("/books/", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    return create_book_in_db(db, book)
@app.get("/books/", response_model=List[BookResponse])
def get_books(db: Session = Depends(get_db)) -> List[BookResponse]:
    return get_all_books_from_db(db)
@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book: BookDB = Depends(validate_book_exists)):
    return book
@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    book: BookDB = Depends(validate_book_exists)
) -> BookResponse:
    return update_book_in_db(db, book, BookUpdate(**book_data.dict()))
@app.patch("/books/{book_id}", response_model=BookResponse)
def partial_update_book(
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    book: BookDB = Depends(validate_book_exists)
) -> BookResponse:
    return update_book_in_db(db, book, book_data)
@app.delete("/books/{book_id}", status_code=204)
def delete_book(
    db: Session = Depends(get_db),
    book: BookDB = Depends(validate_book_exists)
) -> None:
    delete_book_from_db(db, book)