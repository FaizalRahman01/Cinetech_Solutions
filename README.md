# CineTech Solutions

A comprehensive multiplex and entertainment management system.

## Features

- Ticket pricing based on age groups
- Finance management with PIN protection
- Student discount management
- Employee data viewing
- Sales analytics

## Setup

1. Clone the repository
2. Install requirements: `pip install flask`
3. Run the application: `python app.py`
4. Access the web interface at `http://localhost:5000`

## Database

The application uses SQLite for data storage. The database is automatically initialized with:
- Default finance account (PIN: 1234, Balance: $10,000)
- 10 sample employee records
- Empty student records table