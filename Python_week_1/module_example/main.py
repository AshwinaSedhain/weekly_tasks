# main.py
from book import Book
from library import Library

# Create library
my_library = Library()

# Create book objects
book1 = Book("hahahaha", "Ashwini", 18000)
book2 = Book("manxe", "Ashwinaa", 1988)

# Add books to library
my_library.add_book(book1)
my_library.add_book(book2)

# Show all books
my_library.show_books()