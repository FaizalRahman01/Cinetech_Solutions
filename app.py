from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from database import create_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Helper function to get database connection
def get_db_connection():
    conn = create_connection()
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ticket', methods=['GET', 'POST'])
def ticket():
    price = None
    if request.method == 'POST':
        try:
            age = int(request.form['age'])
            if age <= 0:
                flash('Invalid age. Please enter a positive number.', 'error')
            elif age <= 12:
                price = {'type': 'Child Ticket', 'amount': 5}
            elif age <= 18:
                price = {'type': 'Teenager Ticket', 'amount': 8}
            elif age <= 60:
                price = {'type': 'Adult Ticket', 'amount': 12}
            else:
                price = {'type': 'Senior Citizen Ticket', 'amount': 7}
        except ValueError:
            flash('Invalid input. Please enter a valid number.', 'error')
    
    return render_template('ticket.html', price=price)

@app.route('/finance', methods=['GET', 'POST'])
def finance():
    if request.method == 'POST':
        if 'pin' in request.form:  # PIN verification
            try:
                entered_pin = int(request.form['pin'])
                conn = get_db_connection()
                finance_data = conn.execute('SELECT * FROM finance WHERE id = 1').fetchone()
                conn.close()
                
                if entered_pin == finance_data['pin']:
                    session['pin_verified'] = True
                    flash('PIN verified successfully!', 'success')
                else:
                    flash('Incorrect PIN. Please try again.', 'error')
            except ValueError:
                flash('Invalid PIN. Please enter numbers only.', 'error')
        
        elif 'amount' in request.form:  # Deposit or withdraw
            if not session.get('pin_verified'):
                return redirect(url_for('finance'))
            
            try:
                amount = float(request.form['amount'])
                if amount <= 0:
                    flash('Amount must be positive.', 'error')
                    return redirect(url_for('finance'))
                
                conn = get_db_connection()
                finance_data = conn.execute('SELECT * FROM finance WHERE id = 1').fetchone()
                current_balance = finance_data['balance']
                
                if 'deposit' in request.form:
                    new_balance = current_balance + amount
                    conn.execute('UPDATE finance SET balance = ? WHERE id = 1', (new_balance,))
                    conn.commit()
                    flash(f'Deposit successful! New balance: ${new_balance:.2f}', 'success')
                elif 'withdraw' in request.form:
                    if amount > current_balance:
                        flash('Insufficient funds.', 'error')
                    else:
                        new_balance = current_balance - amount
                        conn.execute('UPDATE finance SET balance = ? WHERE id = 1', (new_balance,))
                        conn.commit()
                        flash(f'Withdrawal successful! New balance: ${new_balance:.2f}', 'success')
                
                conn.close()
            except ValueError:
                flash('Invalid amount.', 'error')
    
    # Get current balance
    conn = get_db_connection()
    finance_data = conn.execute('SELECT * FROM finance WHERE id = 1').fetchone()
    conn.close()
    
    return render_template('finance.html', 
                         balance=finance_data['balance'],
                         pin_verified=session.get('pin_verified', False))

@app.route('/finance/logout')
def finance_logout():
    session.pop('pin_verified', None)
    flash('Logged out from finance portal.', 'info')
    return redirect(url_for('finance'))

@app.route('/student', methods=['GET', 'POST'])
def student():
    conn = get_db_connection()
    
    if request.method == 'POST':
        if 'add_student' in request.form:
            name = request.form['name'].strip()
            student_id = request.form['id']
            grades = request.form['grades']
            
            # Validate inputs
            if not name.replace(' ', '').isalpha():
                flash('Invalid name. Only letters and spaces allowed.', 'error')
            else:
                try:
                    student_id = int(student_id)
                    if student_id <= 0:
                        flash('ID must be a positive number.', 'error')
                    else:
                        # Validate grades
                        try:
                            grades_list = [int(g.strip()) for g in grades.split(',')]
                            if not all(0 <= g <= 100 for g in grades_list):
                                flash('Grades must be between 0-100.', 'error')
                            else:
                                # Check if student ID already exists
                                existing = conn.execute('SELECT id FROM students WHERE id = ?', (student_id,)).fetchone()
                                if existing:
                                    flash('Student ID already exists.', 'error')
                                else:
                                    # Add student
                                    conn.execute('''
                                        INSERT INTO students (id, name, grades)
                                        VALUES (?, ?, ?)
                                    ''', (student_id, name, grades))
                                    conn.commit()
                                    avg_grade = sum(grades_list) / len(grades_list)
                                    flash(f'Student {name} added successfully with average grade {avg_grade:.2f}%', 'success')
                        except ValueError:
                            flash('Invalid grades. Must be numbers separated by commas.', 'error')
                except ValueError:
                    flash('Invalid ID. Must be a number.', 'error')
        
        elif 'search_id' in request.form:
            search_id = request.form['search_id']
            try:
                search_id = int(search_id)
                student = conn.execute('SELECT * FROM students WHERE id = ?', (search_id,)).fetchone()
                if student:
                    grades = [int(g) for g in student['grades'].split(',')]
                    avg = sum(grades) / len(grades)
                    session['search_result'] = {
                        'name': student['name'],
                        'id': student['id'],
                        'grades': student['grades'],
                        'average': avg
                    }
                else:
                    flash('Student ID not found', 'error')
            except ValueError:
                flash('Invalid ID. Must be a number.', 'error')
        
        elif 'threshold' in request.form:
            try:
                threshold = float(request.form['threshold'])
                if not 0 <= threshold <= 100:
                    flash('Threshold must be between 0-100', 'error')
                else:
                    students = conn.execute('SELECT * FROM students').fetchall()
                    above_threshold = []
                    
                    for student in students:
                        grades = [int(g) for g in student['grades'].split(',')]
                        avg = sum(grades) / len(grades)
                        if avg > threshold:
                            above_threshold.append({
                                'name': student['name'],
                                'id': student['id'],
                                'average': avg
                            })
                    
                    session['threshold_result'] = {
                        'threshold': threshold,
                        'students': above_threshold
                    }
            except ValueError:
                flash('Invalid threshold. Must be a number.', 'error')
    
    # Get search results from session if they exist
    search_result = session.pop('search_result', None)
    threshold_result = session.pop('threshold_result', None)
    
    conn.close()
    return render_template('student.html', search_result=search_result, threshold_result=threshold_result)

@app.route('/employee')
def employee():
    conn = get_db_connection()
    
    # Get all employees ordered by salary
    employees = conn.execute('''
        SELECT * FROM employees 
        ORDER BY salary DESC
    ''').fetchall()
    
    # Calculate updated salaries (10% increase)
    updated_employees = []
    for emp in employees:
        updated_employees.append({
            'name': emp['name'],
            'salary': emp['salary'] * 1.10
        })
    
    conn.close()
    
    return render_template('employee.html', employees=employees, updated_employees=updated_employees)

@app.route('/sales')
def sales():
    sales_data = [200, 450, 700, 150, 900, 100, 220, 600, 450]
    tax_prices = [round(amount * 1.10, 2) for amount in sales_data]
    high_value = [amount for amount in sales_data if amount > 500]
    total_revenue = sum(tax_prices)
    
    return render_template('sales.html',
                         sales_data=sales_data,
                         tax_prices=tax_prices,
                         high_value=high_value,
                         total_revenue=total_revenue)

if __name__ == '__main__':
    app.run(debug=True)