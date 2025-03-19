import os
import logging
from datetime import datetime
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file, Response
)
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
import gridfs
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")  # Fetch secret key securely

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)  # Timeout after 5s
    client.server_info()  # Force connection to check for errors
except Exception as e:
    logging.error(f"MongoDB Connection Error: {e}")
    exit(1)

# Database & Collections
db = client['rentease']
users_collection = db['users']
properties_collection = db['properties']
tenants_collection = db['tenants']
electricity_bills_collection = db['electricity_bills']
rent_collection = db["rent"]
expenses_collection = db["expenses"]

# Initialize GridFS
fs = gridfs.GridFS(db)

# File Upload Validation
def allowed_file(filename):
    allowed_extensions = {"pdf", "jpg", "jpeg", "png"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


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
from datetime import datetime, timedelta

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    selected_month = request.args.get("month", "")
    tenants = list(tenants_collection.find({}))

    paid_tenants = []
    pending_tenants = []
    overdue_tenants = []
    tenant_billing_data = []

    total_income = 0
    total_electricity_expenses = 0
    total_expenses = 0

    today = datetime.today()
    grace_period_days = 5  # Grace period before marking as overdue

    available_months = set()

    for tenant in tenants:
        rent_due_date_obj = tenant.get("rent_due_date")

        if rent_due_date_obj:
            rent_due_date = rent_due_date_obj if isinstance(rent_due_date_obj, datetime) else datetime.strptime(rent_due_date_obj, "%Y-%m-%d")
            rent_due_day = rent_due_date.day
        else:
            rent_due_day = 1  # Default to the 1st if no due date exists

        for rent_record in tenant.get("rent_history", []):
            available_months.add(rent_record["month"])

            if not selected_month or rent_record["month"] == selected_month:
                total_rent = rent_record["total_rent"]
                paid_amount = rent_record.get("paid_amount", 0)
                remaining_balance = total_rent - paid_amount

                due_date = datetime.strptime(rent_record["month"], "%Y-%m").replace(day=rent_due_day)
                overdue_threshold = due_date + timedelta(days=grace_period_days)
                days_since_due = (today - due_date).days

                tenant_data = {
                    "name": tenant["name"],
                    "phone": tenant["phone_number"],
                    "month": rent_record["month"],
                    "rent": rent_record["rent_amount"],
                    "electricity_bill": rent_record["electricity_bill"],
                    "total_bill": total_rent,
                    "paid_amount": paid_amount,
                    "remaining_balance": remaining_balance,
                }

                if remaining_balance == 0:
                    paid_tenants.append(tenant_data)
                elif remaining_balance > 0 and today <= overdue_threshold:
                    tenant_data["days_pending"] = days_since_due
                    pending_tenants.append(tenant_data)
                else:
                    tenant_data["days_overdue"] = days_since_due - grace_period_days
                    overdue_tenants.append(tenant_data)

                tenant_billing_data.append({
                    "name": tenant["name"],
                    "month": rent_record["month"],
                    "rent": rent_record["rent_amount"],
                    "electricity_bill": rent_record["electricity_bill"],
                    "total_bill": rent_record["total_rent"],
                    "phone": tenant["phone_number"],
                })

                total_income += total_rent
                total_electricity_expenses += rent_record["electricity_bill"]

    expenses_data = list(expenses_collection.find({}))
    total_expenses = sum(expense['amount'] for expense in expenses_data)
    print("Pending Tenants:", pending_tenants)
    print("Overdue Tenants:", overdue_tenants)


    return render_template(
        'dashboard.html',
        paid_tenants=paid_tenants,
        pending_tenants=pending_tenants,
        overdue_tenants=overdue_tenants,
        tenant_billing_data=tenant_billing_data,
        available_months=sorted(available_months),
        selected_month=selected_month,
        total_income=total_income,
        total_electricity_expenses=total_electricity_expenses,
        total_expenses=total_expenses,
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
        deposit_amount = float(request.form.get("deposit"))
        rent_amount = float(request.form.get("rent"))
        lease_start_date = request.form.get("lease_date")
        rent_due_date = request.form.get("rent_due_date")
        initial_meter_reading = int(request.form.get("initial_meter_reading", 0))
        notes = request.form.get("notes")

        # ✅ Handle File Uploads
        aadhaar_file = request.files.get("aadhaar_document")
        pan_file = request.files.get("pan_document")
        photo_file = request.files.get("photo_document")

        # Upload files to GridFS and get their IDs
        documents = {}
        if aadhaar_file:
            documents["aadhaar_document"] = fs.put(aadhaar_file, filename=aadhaar_file.filename)
        if pan_file:
            documents["pan_document"] = fs.put(pan_file, filename=pan_file.filename)
        if photo_file:
            documents["photo_document"] = fs.put(photo_file, filename=photo_file.filename)

        # ✅ Store Tenant Details in MongoDB
        tenant_id = tenants_collection.insert_one({
            "name": name,
            "phone_number": phone_number,
            "unit_type": unit_type,
            "room_number": room_number,
            "rent_amount": rent_amount,
            "deposit_amount": deposit_amount,
            "lease_start_date": datetime.strptime(lease_start_date, "%Y-%m-%d"),
            "rent_due_date": datetime.strptime(rent_due_date, "%Y-%m-%d"),
            "initial_meter_reading": initial_meter_reading,
            "notes": notes,
            "documents": documents,  # Store GridFS file IDs
            "created_at": datetime.utcnow(),
        }).inserted_id

        flash("Tenant added successfully with uploaded documents!", "success")
        return redirect(url_for("add_tenant"))

    units = list(properties_collection.find({}, {"unit_type": 1, "room_numbers": 1}))
    return render_template("add_tenant.html", units=units)


@app.route("/get_document/<document_id>")
def get_document(document_id):
    try:
        # Fetch file from GridFS
        file_data = fs.get(ObjectId(document_id))

        # Extract MIME type and filename (if available)
        content_type = file_data.content_type if hasattr(file_data, 'content_type') else "application/octet-stream"
        file_name = file_data.filename if hasattr(file_data, 'filename') else "file"

        # ✅ Set both `mimetype` and `download_name`
        return send_file(BytesIO(file_data.read()), mimetype=content_type, download_name=file_name, as_attachment=False)

    except gridfs.errors.NoFile:
        return "Document not found", 404

    except Exception as e:
        return f"Error: {str(e)}", 500


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

        # ✅ Fetch last recorded reading OR initial reading if no previous bill
        last_bill = electricity_bills_collection.find_one(
            {"tenant_id": str(tenant_id), "month": {"$lt": month}},
            sort=[("month", -1)]
        )
        if last_bill:
            last_reading = last_bill["current_reading"]
        else:
            # Use initial meter reading from first entry
            initial_bill = electricity_bills_collection.find_one({"tenant_id": str(tenant_id)})
            last_reading = initial_bill["current_reading"] if initial_bill else 0

        units_consumed = max(0, current_reading - last_reading)  # Ensure no negative values
        total_bill = units_consumed * rate_per_unit

        # ✅ Save electricity bill
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
            upsert=True
        )

        # ✅ Update rent history with new bill
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

    # ✅ Fetch available months
    all_months = sorted(
        {bill["month"] for bill in electricity_bills_collection.find({}, {"month": 1})},
        reverse=True
    )

    # ✅ Get selected filters from query params
    selected_month = request.args.get('month', '')  # Selected month filter
    selected_tenant = request.args.get('tenant_filter', '')  # Selected tenant filter

    # ✅ Build query dynamically based on filters
    query = {}
    if selected_month:
        query["month"] = selected_month
    if selected_tenant:
        query["tenant_id"] = selected_tenant  # Keep tenant_id as a string for filtering

    # ✅ Fetch filtered bills and sort by month in descending order
    bills = list(electricity_bills_collection.find(query).sort("month", -1))

    # ✅ Print debug info
    print("Selected Month:", selected_month)
    print("Selected Tenant:", selected_tenant)
    print("Fetched Bills:", bills)  # Debug: Check if bills are fetched correctly

    return render_template(
        'electricity_bill.html',
        tenants=tenants,
        bills=bills,  # ✅ Ensure bills are passed to the template
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

from datetime import datetime, timedelta
from bson.objectid import ObjectId

@app.route('/rent_collection', methods=['GET', 'POST'])
def rent_collection():
    if 'username' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    # Get selected month from query parameters
    selected_month = request.args.get('month', datetime.today().strftime("%Y-%m"))  

    tenants = list(tenants_collection.find({}))

    paid_tenants = []
    pending_tenants = []
    overdue_tenants = []
    today = datetime.today()
    overdue_threshold = today - timedelta(days=5)

    for tenant in tenants:
        rent_record = next((r for r in tenant.get("rent_history", []) if r["month"] == selected_month), None)

        if rent_record:
            total_rent = rent_record["total_rent"]
            paid_amount = rent_record.get("paid_amount", 0)  # Default to 0 if not available
            remaining_balance = total_rent - paid_amount

            tenant_data = {
                "id": str(tenant["_id"]),
                "name": tenant["name"],
                "phone": tenant["phone_number"],
                "room_number": tenant["room_number"],
                "total_rent": total_rent,
                "paid_amount": paid_amount,
                "remaining_balance": remaining_balance
            }

            if remaining_balance == 0:
                paid_tenants.append(tenant_data)
            elif remaining_balance > 0 and datetime.strptime(rent_record["month"], "%Y-%m") > overdue_threshold:
                pending_tenants.append(tenant_data)
            else:
                overdue_tenants.append(tenant_data)

    available_months = sorted(
        {r["month"] for t in tenants for r in t.get("rent_history", [])},
        reverse=True
    )

    return render_template(
        'rent_collection.html',
        paid_tenants=paid_tenants,
        pending_tenants=pending_tenants,
        overdue_tenants=overdue_tenants,
        available_months=available_months,
        selected_month=selected_month
    )
    

@app.route('/update_rent_payment', methods=['POST'])
def update_rent_payment():
    if 'username' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    tenant_id = request.form.get('tenant_id')
    month = request.form.get('month')
    paid_amount = float(request.form.get('paid_amount'))

    tenant = tenants_collection.find_one({"_id": ObjectId(tenant_id)})
    if not tenant:
        flash("Tenant not found!", "danger")
        return redirect(url_for('rent_collection'))

    rent_record = next((r for r in tenant.get("rent_history", []) if r["month"] == month), None)

    if not rent_record:
        flash("No rent record found for the selected month!", "danger")
        return redirect(url_for('rent_collection'))

    total_rent = rent_record["total_rent"]
    previous_paid_amount = rent_record.get("paid_amount", 0)
    new_paid_amount = previous_paid_amount + paid_amount
    remaining_balance = total_rent - new_paid_amount

    tenants_collection.update_one(
        {"_id": ObjectId(tenant_id), "rent_history.month": month},
        {"$set": {
            "rent_history.$.paid_amount": new_paid_amount,
            "rent_history.$.remaining_balance": remaining_balance
        }}
    )

    flash(f"Payment updated! Remaining balance: ₹{remaining_balance}", "success")
    return redirect(url_for('rent_collection', month=month))


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))



# if __name__ == '__main__':
#     app.run(debug=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
