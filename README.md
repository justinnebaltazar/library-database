# Library Database Management System

A relational database system designed to manage core library operations.  
Developed with **SQL** and **Python**, including an optional **Qt GUI** for user interaction.  

---

## Features
- **Relational Database Design**  
  - Defined project specifications, ER diagrams, and SQL schemas  
  - Accurate and robust data modeling of library entities (books, patrons, staff, events, transactions, etc.)

- **Graphical User Interface (GUI)**  
  - Built with **Python (Qt)**  
  - Supports 10 core library functions:
    - Book search  
    - Borrow/return books  
    - Patron management  
    - Event registration  
    - Help from librarian  
    - Staff management
    - Volunteer registration
    - Acquistion requests
    - Donation management

- **Role-Based Access Control**  
  - Patrons: search books, borrow/return items, register for events, request help from librarians, volunteer at the library  
  - Staff: manage book inventory, update patron accounts, oversee donations and volunteers, and support library operations

---

## Tech Stack
- **Programming Languages:** Python, SQL
- **Database:** Relational database (SQL-based)  
- **GUI Framework:** Qt (PyQt/PySide)  
- **Testing:** Functional and end-to-end scenario testing  

---

## Future Improvements
- Transition the system to a **web application using React.js** (in progress) for improved accessibility and user experience 
- Add advanced search and filtering options
- Create analytics features to track patron activity