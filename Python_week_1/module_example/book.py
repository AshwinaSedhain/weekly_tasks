# book.py module

class Book:
    def __init__(self, title, author, year):
        self.title = title
        self.author = author
        self.year = year

    def display_info(self):
        return f"'{self.title}' by {self.author}, published in {self.year}"