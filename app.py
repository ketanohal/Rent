from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from bson import ObjectId
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS if your frontend is separate
app.secret_key = 'your_secret_key'  # For session management

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")  # Fetching the URI from environment variable
client = MongoClient(MONGO_URI)
db = client['rentease']  # Database name
users_collection = db['users']  # Users Collection
properties_collection = db['properties']  # Properties Collection
tenants_collection = db['tenants']  # Tenants Collection
electricity_bills_collection = db['electricity_bills']  # Collection for storing electricity bills
rent_collection = db["rent"]  # Collection storing rent details ✅ ADDED THIS
expenses_collection = db["expenses"]




UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def home():
    """Render the homepage."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash("Login Successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid Username or Password", "danger")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if not email or not username or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))

        if users_collection.find_one({"username": username}):
            flash("Username already exists.", "danger")
            return redirect(url_for('register'))
        if users_collection.find_one({"email": email}):
            flash("Email already registered.", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='scrypt')

        users_collection.insert_one({
            "email": email,
            "username": username,
            "password": hashed_password
        })

        flash("Registration Successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    selected_month = request.args.get("month")  # Get selected month from query params
    tenants = list(tenants_collection.find({}))  # Fetch all tenants
    tenant_billing_data = []

    total_income = 0
    total_electricity_expenses = 0
    total_expenses = 0

    for tenant in tenants:
        for rent_record in tenant.get("rent_history", []):  # Extract rent history
            # If a month is selected, filter the data
            if not selected_month or rent_record["month"] == selected_month:
                tenant_billing_data.append({
                    "name": tenant["name"],
                    "month": rent_record["month"],
                    "rent": rent_record["rent_amount"],
                    "electricity_bill": rent_record["electricity_bill"],
                    "total_bill": rent_record["total_rent"],
                    "phone": tenant["phone_number"]
                })

                # Calculate total income (sum of total_bill for each tenant)
                total_income += rent_record["total_rent"]
                # Calculate total electricity expenses (sum of electricity bills for each tenant)
                total_electricity_expenses += rent_record["electricity_bill"]

    # Get unique months available in the database for filtering options
    available_months = sorted(
        {rent["month"] for tenant in tenants for rent in tenant.get("rent_history", [])}
    )

    # Fetch all expenses from the expenses collection and calculate total expenses
    expenses_data = list(expenses_collection.find({}))
    total_expenses = sum(expense['amount'] for expense in expenses_data)

    return render_template(
        'dashboard.html',
        username=session['username'],
        tenant_billing_data=tenant_billing_data,
        available_months=available_months,
        selected_month=selected_month,
        total_income=total_income,  # Pass total income to the template
        total_electricity_expenses=total_electricity_expenses,  # Pass total electricity expenses to the template
        total_expenses=total_expenses  # Pass total expenses (only from the expenses collection)
    )



@app.route('/property')
def property():
    """Display all properties."""
    if 'username' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    properties = list(properties_collection.find({}, {"_id": 0}))
    return render_template('property.html', properties=properties)


@app.route('/add_unit', methods=['GET', 'POST'])
def add_unit():
    if request.method == 'POST':
        unit_type = request.form.get('unit_type')
        unit_count = int(request.form.get('unit_count', 0))

        if not unit_type or unit_count <= 0:
            flash("All fields are required and number of units should be greater than 0!", "danger")
            return redirect(url_for('add_unit'))

        existing_unit = properties_collection.find_one({"unit_type": unit_type})

        if existing_unit:
            current_count = existing_unit["unit_count"]
            new_rooms = [current_count + i + 1 for i in range(unit_count)]  

            properties_collection.update_one(
                {"unit_type": unit_type},
                {
                    "$inc": {"unit_count": unit_count},
                    "$push": {"room_numbers": {"$each": new_rooms}},
                }
            )
        else:
            room_numbers = list(range(1, unit_count + 1))

            properties_collection.insert_one({
                "unit_type": unit_type,
                "unit_count": unit_count,
                "room_numbers": room_numbers,
                "assigned_rooms": []
            })

        flash("Unit added successfully!", "success")
        return redirect(url_for('add_unit'))

    units = list(properties_collection.find({}, {"_id": 0}))
    return render_template('add_unit.html', units=units)


@app.route("/add_tenant", methods=["GET", "POST"])
def add_tenant():
    if 'username' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    if request.method == "POST":
        name = request.form.get("tenant_name")
        phone_number = request.form.get("phone")
        unit_type = request.form.get("unit_type")
        room_number = int(request.form.get("room_number"))
        rent_amount = request.form.get("rent")
        lease_start_date = request.form.get("lease_date")

        if not name or not phone_number or not unit_type or not room_number or not rent_amount or not lease_start_date:
            flash("Mandatory fields are missing!", "danger")
            return redirect(url_for("add_tenant"))

        unit_data = properties_collection.find_one({"unit_type": unit_type})
        if not unit_data or room_number not in unit_data.get("room_numbers", []) or room_number in unit_data.get("assigned_rooms", []):
            flash("Selected room is no longer available.", "danger")
            return redirect(url_for("add_tenant"))

        tenants_collection.insert_one({
            "name": name,
            "phone_number": phone_number,
            "unit_type": unit_type,
            "room_number": room_number,
            "rent_amount": rent_amount,
            "lease_start_date": datetime.strptime(lease_start_date, "%Y-%m-%d"),
            "created_at": datetime.utcnow(),
        })

        properties_collection.update_one(
            {"unit_type": unit_type},
            {"$pull": {"room_numbers": room_number}, "$push": {"assigned_rooms": room_number}}
        )

        flash("Tenant added successfully!", "success")
        return redirect(url_for("add_tenant"))

    units = list(properties_collection.find({}, {"unit_type": 1, "room_numbers": 1}))
    return render_template("add_tenant.html", units=units)


@app.route("/get_rooms")
def get_rooms():
    unit_type = request.args.get("unit_type")
    unit_data = properties_collection.find_one({"unit_type": unit_type}, {"room_numbers": 1, "assigned_rooms": 1})

    if not unit_data:
        return jsonify({"rooms": []})

    available_rooms = [room for room in unit_data["room_numbers"] if room not in unit_data.get("assigned_rooms", [])]
    return jsonify({"rooms": available_rooms})



# Display All Tenants
@app.route('/tenants')
def tenants():
    if 'username' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    tenants = list(tenants_collection.find({}, {"_id": 1, "name": 1, "phone_number": 1, "unit_type": 1, "rent_amount": 1, "lease_start_date": 1}))
    return render_template('tenants.html', tenants=tenants)

# Tenant Details Page
@app.route('/tenant/<tenant_id>')
def tenant_details(tenant_id):
    tenant = tenants_collection.find_one({"_id": ObjectId(tenant_id)})

    if not tenant:
        flash("Tenant not found!", "danger")
        return redirect(url_for('tenants'))

    # Fetch rent history from tenant's document
    rent_history = tenant.get("rent_history", [])  # Default to empty list if not found

    # Calculate total rent paid from rent history
    total_rent_paid = sum(rent.get("total_rent", 0) for rent in rent_history)

    return render_template('tenant_details.html', tenant=tenant, rent_history=rent_history, total_rent_paid=total_rent_paid)


@app.route('/electricity_bill', methods=['GET', 'POST'])
def electricity_bill():
    if 'username' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    tenants = list(tenants_collection.find({}, {"_id": 1, "name": 1, "room_number": 1}))

    if request.method == 'POST':
        tenant_id = request.form.get('tenant_id')
        tenant = tenants_collection.find_one({"_id": ObjectId(tenant_id)})

        if not tenant:
            flash("Invalid Tenant selected!", "danger")
            return redirect(url_for('electricity_bill'))

        tenant_name = tenant.get('name', 'Unknown')
        room_number = tenant.get('room_number', 'N/A')

        date = request.form.get('date')  # YYYY-MM-DD
        month = date[:7]  # Extract YYYY-MM format

        current_reading = int(request.form.get('current_reading'))
        rate_per_unit = float(request.form.get('rate_per_unit'))

        # Fetch last recorded reading (only for past months)
        last_bill = electricity_bills_collection.find_one(
            {"tenant_id": str(tenant_id), "month": {"$lt": month}},
            sort=[("month", -1)]
        )
        last_reading = last_bill['current_reading'] if last_bill else 0

        units_consumed = current_reading - last_reading
        total_bill = units_consumed * rate_per_unit

        # Save electricity bill
        electricity_bills_collection.update_one(
            {"tenant_id": str(tenant_id), "month": month},
            {"$set": {
                "tenant_id": str(tenant_id),
                "tenant_name": tenant_name,
                "room_number": room_number,
                "month": month,
                "last_reading": last_reading,
                "current_reading": current_reading,
                "units_consumed": units_consumed,
                "rate_per_unit": rate_per_unit,
                "total_bill": total_bill
            }},
            upsert=True  # Create new record if not exists
        )

        # Fetch tenant rent and update total rent
        rent_amount = float(tenant.get("rent_amount", 0))
        total_rent = rent_amount + total_bill

        tenants_collection.update_one(
            {"_id": ObjectId(tenant_id)},
            {"$push": {
                "rent_history": {
                    "month": month,
                    "rent_amount": rent_amount,
                    "electricity_bill": total_bill,
                    "total_rent": total_rent
                }
            }}
        )

        flash("Electricity bill recorded and rent updated successfully!", "success")
        return redirect(url_for('electricity_bill'))

    # 🔹 Get selected filters from query params
    selected_month = request.args.get('month', '')  # Selected month filter
    selected_tenant = request.args.get('tenant_filter', '')  # Selected tenant filter

    # 🔹 Build query dynamically based on filters
    query = {}
    if selected_month:
        query["month"] = selected_month
    if selected_tenant:
        query["tenant_id"] = selected_tenant  # Keep tenant_id as a string for filtering

    # 🔹 Fetch filtered bills and sort by month in descending order
    bills = list(electricity_bills_collection.find(query).sort("month", -1))

    # 🔹 Get all available months for filtering (also sorted in descending order)
    all_months = sorted(
        {bill["month"] for bill in electricity_bills_collection.find({}, {"month": 1})},
        reverse=True
    )

    return render_template(
        'electricity_bill.html',
        tenants=tenants,
        bills=bills,
        all_months=all_months,
        selected_month=selected_month,
        selected_tenant=selected_tenant
    )

@app.route('/calculate_total_rent', methods=['POST'])
def calculate_total_rent():
    """Automatically calculate total rent including electricity bill."""
    tenant_id = request.form['tenant_id']
    month = request.form['month']

    tenant = tenants_collection.find_one({"_id": ObjectId(tenant_id)})

    if not tenant:
        flash("Tenant not found!", "danger")
        return redirect(url_for('tenants'))

    rent_amount = float(tenant.get("rent_amount", 0))  # Ensure rent_amount is treated as float

    # Fetch electricity bill for the tenant in the selected month
    electricity_bill = electricity_bills_collection.find_one({"tenant_id": tenant_id, "month": month})
    electricity_bill_amount = float(electricity_bill["total_bill"]) if electricity_bill else 0

    # Calculate total rent (Base Rent + Electricity Bill)
    total_rent = rent_amount + electricity_bill_amount

    # Update the tenant's rent history
    tenants_collection.update_one(
        {"_id": ObjectId(tenant_id)},
        {"$push": {
            "rent_history": {
                "month": month,
                "rent_amount": rent_amount,
                "electricity_bill": electricity_bill_amount,
                "total_rent": total_rent
            }
        }}
    )

    flash(f"Total rent for {month} calculated successfully!", "success")
    return redirect(url_for('tenant_details', tenant_id=tenant_id))


@app.route('/expenses')
def expenses():
    expenses_list = list(expenses_collection.find({}))
    return render_template("expenses.html", expenses=expenses_list)

from datetime import datetime

@app.route('/add_expense', methods=['POST'])
def add_expense():
    name = request.form.get("name")
    amount = request.form.get("amount")
    date_str = request.form.get("date")  # Get the date input (in 'YYYY-MM-DD' format)

    if name and amount and date_str:
        # Convert the date string to a datetime object
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        month = date_obj.strftime("%B")  # Get month name (e.g., January, February, etc.)
        year = date_obj.year  # Get year

        # Save the expense along with month and year
        expenses_collection.insert_one({
            "name": name,
            "amount": float(amount),
            "date": date_obj,
            "month": month,
            "year": year
        })

    return redirect(url_for('expenses'))


@app.route('/delete_expense/<expense_id>', methods=['POST'])
def delete_expense(expense_id):
    expenses_collection.delete_one({"_id": ObjectId(expense_id)})
    return redirect(url_for('expenses'))

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    if request.method == 'POST':
        selected_month = request.form.get('month')
        selected_year = request.form.get('year')

        # Fetch all expenses for the selected month and year
        expenses_list = list(expenses_collection.find({"month": selected_month, "year": int(selected_year)}))

        # Calculate total expenses for the selected month and year
        total_expenses = sum(expense['amount'] for expense in expenses_list)

        return render_template('reports.html', expenses=expenses_list, total_expenses=total_expenses)

    return render_template('reports.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
