import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://ridujyaocuehqp:f932b365d5a6e286f39a67c399d74e85ce7565160a7f4728bc3f4ca4c7873a92@ec2-75-101-131-79.compute-1.amazonaws.com:5432/dav50ftnrmju6q")
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book name {title} from {author} from year {year} to table.")
    db.commit()


if __name__ == "__main__":
    main()
