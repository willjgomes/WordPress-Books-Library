

import wpg_book_post
from wpg_book_post import WPGBook as WPGBook

import book_csv_reader

#Read CSV file contain book information
csv_file_path = "C:\data\local_booklist.csv"
book_count = 0
for record in book_csv_reader.read_csv_file(csv_file_path):
    book_count += 1
    
    new_book = WPGBook(
        record['BookTitle'], 
        "", 
        record['FirstName'] + " " + record['LastName'],
        record['AuthorFolder'],
        record['BookFile'],
        record['BookCoverFile'],
        record['BasePath']
        )
    
    #if (book_count <= 1):
    wpg_book_post.createBook(new_book)
    #print(new_book)

print(f"Books processed {book_count}")
