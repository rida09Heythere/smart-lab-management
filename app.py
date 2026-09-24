from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config, get_connection
from datetime import datetime, timedelta


app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():
    if "user_id" in session:
        if session.get("role") == "Student":
            return redirect(url_for("user_dashboard"))
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ==========================================================
# ADMIN LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        if session.get("role") == "Student":
            return redirect(url_for("user_dashboard"))
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s
            AND role = 'Admin'
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and check_password_hash(user["password"], password):

            session.clear()

            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            flash("Login successful!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid administrator email or password.", "danger")

    return render_template("login.html")


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return redirect(url_for("user_dashboard"))

    connection = get_connection()
    cursor = connection.cursor()

    # Total Laboratories
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM laboratories
    """)
    total_labs = cursor.fetchone()["total"]

    # Total Computers
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM computers
    """)
    total_computers = cursor.fetchone()["total"]

    # Total Complaints
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM complaints
    """)
    total_complaints = cursor.fetchone()["total"]

    # Pending Complaints
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM complaints
        WHERE status = 'Pending'
    """)
    pending_complaints = cursor.fetchone()["total"]

    # In Progress Complaints
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM complaints
        WHERE status = 'In Progress'
    """)
    in_progress_complaints = cursor.fetchone()["total"]

    # Solved Complaints
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM complaints
        WHERE status = 'Solved'
    """)
    solved_complaints = cursor.fetchone()["total"]

    # Active Maintenance
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM complaints
        WHERE status = 'In Progress'
    """)
    total_maintenance = cursor.fetchone()["total"]
    # Total Inventory Items
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM inventory
    """)
    total_inventory = cursor.fetchone()["total"]

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        total_labs=total_labs,
        total_computers=total_computers,
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        in_progress_complaints=in_progress_complaints,
        solved_complaints=solved_complaints,
        total_maintenance=total_maintenance,
        total_inventory=total_inventory
    )
# ==========================================================
# LABORATORIES
# ==========================================================

@app.route("/laboratories")
def laboratories():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM laboratories
        ORDER BY lab_number
        """
    )

    laboratories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "laboratories.html",
        laboratories=laboratories
    )


# ==========================================================
# ADD LABORATORY
# ==========================================================

@app.route("/add_lab", methods=["GET", "POST"])
def add_lab():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        lab_number = request.form.get("lab_number", "").strip()
        floor = request.form.get("floor", "").strip()
        capacity = request.form.get("capacity", "").strip()
        status = request.form.get("status", "").strip()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT lab_id
            FROM laboratories
            WHERE lab_number = %s
            """,
            (lab_number,)
        )

        existing_lab = cursor.fetchone()

        if existing_lab:

            cursor.close()
            connection.close()

            flash(
                f"Lab {lab_number} already exists.",
                "warning"
            )

            return redirect(url_for("add_lab"))

        cursor.execute(
            """
            INSERT INTO laboratories
            (
                lab_number,
                floor,
                capacity,
                status
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                lab_number,
                floor,
                capacity,
                status
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Laboratory added successfully!",
            "success"
        )

        return redirect(url_for("laboratories"))

    return render_template("add_lab.html")


# ==========================================================
# EDIT LABORATORY
# ==========================================================

@app.route("/edit_lab/<int:lab_id>", methods=["GET", "POST"])
def edit_lab(lab_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    if request.method == "POST":

        lab_number = request.form.get("lab_number", "").strip()
        floor = request.form.get("floor", "").strip()
        capacity = request.form.get("capacity", "").strip()
        status = request.form.get("status", "").strip()

        cursor.execute(
            """
            SELECT lab_id
            FROM laboratories
            WHERE lab_number = %s
            AND lab_id != %s
            """,
            (
                lab_number,
                lab_id
            )
        )

        duplicate = cursor.fetchone()

        if duplicate:

            cursor.close()
            connection.close()

            flash(
                f"Lab {lab_number} already exists.",
                "warning"
            )

            return redirect(
                url_for("edit_lab", lab_id=lab_id)
            )

        cursor.execute(
            """
            UPDATE laboratories
            SET
                lab_number = %s,
                floor = %s,
                capacity = %s,
                status = %s
            WHERE lab_id = %s
            """,
            (
                lab_number,
                floor,
                capacity,
                status,
                lab_id
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Laboratory updated successfully!",
            "success"
        )

        return redirect(url_for("laboratories"))

    cursor.execute(
        """
        SELECT *
        FROM laboratories
        WHERE lab_id = %s
        """,
        (lab_id,)
    )

    lab = cursor.fetchone()

    cursor.close()
    connection.close()

    if not lab:
        flash("Laboratory not found.", "danger")
        return redirect(url_for("laboratories"))

    return render_template(
        "edit_lab.html",
        lab=lab
    )


# ==========================================================
# DELETE LABORATORY
# ==========================================================

@app.route("/delete_lab/<int:lab_id>")
def delete_lab(lab_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM laboratories
        WHERE lab_id = %s
        """,
        (lab_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    flash(
        "Laboratory deleted successfully!",
        "success"
    )

    return redirect(url_for("laboratories"))
# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(url_for("login"))


# ==========================================================
# COMPUTERS
# ==========================================================

@app.route("/computers")
def computers():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            computers.*,
            laboratories.lab_number
        FROM computers
        JOIN laboratories
            ON computers.lab_id = laboratories.lab_id
        ORDER BY computers.pc_number
        """
    )

    computers = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "computers.html",
        computers=computers
    )


# ==========================================================
# ADD COMPUTER
# ==========================================================

@app.route("/add_computer", methods=["GET", "POST"])
def add_computer():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT lab_id, lab_number
        FROM laboratories
        ORDER BY lab_number
        """
    )

    laboratories = cursor.fetchall()

    if request.method == "POST":

        lab_id = request.form.get("lab_id")
        pc_number = request.form.get("pc_number", "").strip()
        processor = request.form.get("processor", "").strip()
        ram_gb = request.form.get("ram_gb")
        storage_gb = request.form.get("storage_gb")
        operating_system = request.form.get(
            "operating_system",
            ""
        ).strip()
        status = request.form.get("status", "").strip()
        purchase_date = request.form.get("purchase_date") or None
        last_service = request.form.get("last_service") or None
        remarks = request.form.get("remarks", "").strip()

        cursor.execute(
            """
            INSERT INTO computers
            (
                lab_id,
                pc_number,
                processor,
                ram_gb,
                storage_gb,
                operating_system,
                status,
                purchase_date,
                last_service,
                remarks
            )
            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """,
            (
                lab_id,
                pc_number,
                processor,
                ram_gb,
                storage_gb,
                operating_system,
                status,
                purchase_date,
                last_service,
                remarks
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Computer added successfully!",
            "success"
        )

        return redirect(url_for("computers"))

    cursor.close()
    connection.close()

    return render_template(
        "add_computer.html",
        laboratories=laboratories
    )


# ==========================================================
# EDIT COMPUTER
# ==========================================================

@app.route(
    "/edit_computer/<int:computer_id>",
    methods=["GET", "POST"]
)
def edit_computer(computer_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT lab_id, lab_number
        FROM laboratories
        ORDER BY lab_number
        """
    )

    laboratories = cursor.fetchall()

    cursor.execute(
        """
        SELECT *
        FROM computers
        WHERE computer_id = %s
        """,
        (computer_id,)
    )

    computer = cursor.fetchone()

    if not computer:

        cursor.close()
        connection.close()

        flash(
            "Computer not found.",
            "danger"
        )

        return redirect(url_for("computers"))

    if request.method == "POST":

        lab_id = request.form.get("lab_id")
        pc_number = request.form.get("pc_number", "").strip()
        processor = request.form.get("processor", "").strip()
        ram_gb = request.form.get("ram_gb")
        storage_gb = request.form.get("storage_gb")
        operating_system = request.form.get(
            "operating_system",
            ""
        ).strip()
        status = request.form.get("status", "").strip()
        purchase_date = request.form.get("purchase_date") or None
        last_service = request.form.get("last_service") or None
        remarks = request.form.get("remarks", "").strip()

        cursor.execute(
            """
            UPDATE computers
            SET
                lab_id = %s,
                pc_number = %s,
                processor = %s,
                ram_gb = %s,
                storage_gb = %s,
                operating_system = %s,
                status = %s,
                purchase_date = %s,
                last_service = %s,
                remarks = %s
            WHERE computer_id = %s
            """,
            (
                lab_id,
                pc_number,
                processor,
                ram_gb,
                storage_gb,
                operating_system,
                status,
                purchase_date,
                last_service,
                remarks,
                computer_id
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Computer updated successfully!",
            "success"
        )

        return redirect(url_for("computers"))

    cursor.close()
    connection.close()

    return render_template(
        "edit_computer.html",
        computer=computer,
        laboratories=laboratories
    )


# ==========================================================
# DELETE COMPUTER
# ==========================================================

@app.route("/delete_computer/<int:computer_id>")
def delete_computer(computer_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM computers
        WHERE computer_id = %s
        """,
        (computer_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    flash(
        "Computer deleted successfully!",
        "success"
    )

    return redirect(url_for("computers"))


# ==========================================================
# COMPLAINTS
# ==========================================================

@app.route("/complaints")
def complaints():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return redirect(url_for("user_dashboard"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            complaints.*,
            laboratories.lab_number,
            computers.pc_number
        FROM complaints
        LEFT JOIN laboratories
            ON complaints.lab_id = laboratories.lab_id
        LEFT JOIN computers
            ON complaints.computer_id = computers.computer_id
        WHERE complaints.status IN ('Pending', 'In Progress')
        ORDER BY complaints.created_at DESC
        """
    )

    complaints = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "complaints.html",
        complaints=complaints
    )

# ==========================================================
# ADD COMPLAINT
# ==========================================================

@app.route("/add_complaint", methods=["GET", "POST"])
def add_complaint():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT lab_id, lab_number
        FROM laboratories
        ORDER BY lab_number
        """
    )

    laboratories = cursor.fetchall()

    cursor.execute(
        """
        SELECT computer_id, lab_id, pc_number
        FROM computers
        ORDER BY pc_number
        """
    )

    computers = cursor.fetchall()

    if request.method == "POST":

        lab_id = request.form.get("lab_id")
        computer_id = request.form.get("computer_id") or None
        category = request.form.get("category", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get(
            "description",
            ""
        ).strip()
        priority = request.form.get("priority", "").strip()

        cursor.execute(
            """
            INSERT INTO complaints
            (
                user_id,
                lab_id,
                computer_id,
                category,
                title,
                description,
                priority,
                status
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                lab_id,
                computer_id,
                category,
                title,
                description,
                priority,
                "Pending"
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Complaint added successfully!",
            "success"
        )

        return redirect(url_for("complaints"))

    cursor.close()
    connection.close()

    return render_template(
        "add_complaint.html",
        laboratories=laboratories,
        computers=computers
    )
# ==========================================================
# EDIT COMPLAINT
# ==========================================================

# ==========================================================
# ADMIN - UPDATE COMPLAINT STATUS
# ==========================================================

@app.route("/update_complaint/<int:complaint_id>", methods=["POST"])
def update_complaint(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return redirect(url_for("dashboard"))

    status = request.form.get("status")
    remarks = request.form.get("remarks", "").strip()

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Solved",
        "Could Not be Resolved"
    ]

    if status not in allowed_statuses:
        flash("Invalid complaint status.", "danger")
        return redirect(url_for("complaints"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE complaints
        SET
            status = %s,
            remarks = %s,
            resolved_at =
                CASE
                    WHEN %s IN ('Solved', 'Could Not be Resolved')
                    THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END
        WHERE complaint_id = %s
    """, (
        status,
        remarks if remarks else None,
        status,
        complaint_id
    ))

    connection.commit()

    cursor.close()
    connection.close()

    flash("Complaint status updated successfully!", "success")

    return redirect(url_for("complaints"))

# ==========================================================
# DELETE COMPLAINT
# ==========================================================

@app.route("/delete_complaint/<int:complaint_id>")
def delete_complaint(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM complaints
        WHERE complaint_id = %s
        """,
        (complaint_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    flash(
        "Complaint deleted successfully!",
        "success"
    )

    return redirect(url_for("complaints"))


# ==========================================================
# MAINTENANCE
# ==========================================================

@app.route("/maintenance")
def maintenance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            complaints.complaint_id,
            complaints.title,
            complaints.status,
            complaints.priority,
            laboratories.lab_number,
            computers.pc_number
        FROM complaints
        LEFT JOIN laboratories
            ON complaints.lab_id = laboratories.lab_id
        LEFT JOIN computers
            ON complaints.computer_id = computers.computer_id
        WHERE complaints.status IN
            ('Pending', 'In Progress')
        ORDER BY
            complaints.priority DESC,
            complaints.complaint_id DESC
        """
    )

    maintenance_records = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "maintenance.html",
        maintenance_records=maintenance_records
    )


# ==========================================================
# INVENTORY
# ==========================================================

@app.route("/inventory")
def inventory():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM inventory
        ORDER BY item_name
        """
    )

    inventory_items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "inventory.html",
        inventory_items=inventory_items
    )


# ==========================================================
# ADD INVENTORY
# ==========================================================

@app.route("/add_inventory", methods=["GET", "POST"])
def add_inventory():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        category = request.form.get(
            "category",
            ""
        ).strip()

        item_name = category

        quantity = request.form.get(
            "quantity"
        )

        unit = request.form.get(
            "unit",
            ""
        ).strip()

        minimum_stock = request.form.get(
            "minimum_stock"
        )

        location = request.form.get(
            "location",
            ""
        ).strip()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO inventory
            (
                item_name,
                category,
                quantity,
                unit,
                minimum_stock,
                location
            )
            VALUES
            (%s, %s, %s, %s, %s, %s)
            """,
            (
                item_name,
                category,
                quantity,
                unit,
                minimum_stock,
                location
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Inventory item added successfully!",
            "success"
        )

        return redirect(url_for("inventory"))

    return render_template("add_inventory.html")


# ==========================================================
# EDIT INVENTORY
# ==========================================================

@app.route(
    "/edit_inventory/<int:inventory_id>",
    methods=["GET", "POST"]
)
def edit_inventory(inventory_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    categories = [
        "CPU",
        "Monitor",
        "Keyboard",
        "Mouse",
        "Projector",
        "Printer",
        "UPS",
        "RAM",
        "SSD",
        "HDD",
        "LAN Cable",
        "HDMI Cable",
        "Router",
        "Switch",
        "Networking",
        "Electrical",
        "Other"
    ]

    if request.method == "POST":

        category = request.form.get(
            "category",
            ""
        ).strip()

        quantity = request.form.get(
            "quantity"
        )

        unit = request.form.get(
            "unit",
            ""
        ).strip()

        minimum_stock = request.form.get(
            "minimum_stock"
        )

        location = request.form.get(
            "location",
            ""
        ).strip()

        cursor.execute(
            """
            UPDATE inventory
            SET
                item_name = %s,
                category = %s,
                quantity = %s,
                unit = %s,
                minimum_stock = %s,
                location = %s
            WHERE inventory_id = %s
            """,
            (
                category,
                category,
                quantity,
                unit,
                minimum_stock,
                location,
                inventory_id
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Inventory item updated successfully!",
            "success"
        )

        return redirect(url_for("inventory"))

    cursor.execute(
        """
        SELECT *
        FROM inventory
        WHERE inventory_id = %s
        """,
        (inventory_id,)
    )

    item = cursor.fetchone()

    cursor.close()
    connection.close()

    if not item:
        flash(
            "Inventory item not found.",
            "danger"
        )

        return redirect(url_for("inventory"))

    return render_template(
        "edit_inventory.html",
        item=item,
        categories=categories
    )


# ==========================================================
# DELETE INVENTORY
# ==========================================================

@app.route(
    "/delete_inventory/<int:inventory_id>"
)
def delete_inventory(inventory_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM inventory
        WHERE inventory_id = %s
        """,
        (inventory_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    flash(
        "Inventory item deleted successfully!",
        "success"
    )

    return redirect(url_for("inventory"))
############################################################
#REGISTRATION
#==========================================================
@app.route("/student-signup", methods=["GET", "POST"])
def student_signup():

    if request.method == "POST":

        student_id = request.form.get("student_id", "").strip()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()
        phone = request.form.get("phone", "").strip()

        if not student_id or not full_name or not email or not password or not department:
            return render_template(
                "student_signup.html",
                error="Please fill in all required fields."
            )

        if len(password) < 8:
            return render_template(
                "student_signup.html",
                error="Password must be at least 8 characters long."
            )

        connection = get_connection()
        cursor = connection.cursor()

        # Check whether Student ID or email already exists
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE student_id = %s OR email = %s
        """, (student_id, email))

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            connection.close()

            return render_template(
                "student_signup.html",
                error="Student ID or email is already registered."
            )

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (
                student_id,
                full_name,
                email,
                password,
                role,
                department,
                phone
            )
            VALUES
            (%s, %s, %s, %s, 'Student', %s, %s)
        """, (
            student_id,
            full_name,
            email,
            hashed_password,
            department,
            phone
        ))

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Student account created successfully. You can now log in.",
            "success"
        )

        return redirect(url_for("user_login"))

    return render_template("student_signup.html")
# ==========================================================
# STUDENT LOGIN
# ==========================================================
@app.route("/user-login", methods=["GET", "POST"])
def user_login():

    if request.method == "POST":

        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE student_id = %s
            AND role = 'Student'
        """, (student_id,))

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:

            stored_password = str(user["password"])

            # Check hashed password
            if check_password_hash(stored_password, password):

                session.clear()

                session["user_id"] = user["user_id"]
                session["full_name"] = user["full_name"]
                session["email"] = user["email"]
                session["role"] = "Student"
                session["student_id"] = user["student_id"]

                return redirect(url_for("user_dashboard"))

        return render_template(
            "user_login.html",
            error="Invalid Student ID or password."
        )

    return render_template("user_login.html")
########################################################

@app.route("/user-dashboard")
def user_dashboard():

    if "user_id" not in session or session.get("role") != "Student":
        return redirect(url_for("user_login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id, full_name, email, role, department
        FROM users
        WHERE user_id = %s
    """, (session["user_id"],))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user or user["role"] != "Student":
        session.clear()
        return redirect(url_for("user_login"))

    return render_template(
        "user_dashboard.html",
        user=user
    )
#############################################################

# ==========================================================
# ERROR PAGES
# ==========================================================

@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template(
        "500.html"
    ), 500


# ==========================================================
# STUDENT COMPLAINTS
# ==========================================================

@app.route("/student-complaints")
def student_complaints():

    if "user_id" not in session or session.get("role") != "Student":
        return redirect(url_for("user_login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            complaints.complaint_id,
            complaints.title,
            complaints.description,
            complaints.category,
            complaints.priority,
            complaints.status,
            complaints.created_at,
            laboratories.lab_number,
            computers.pc_number
        FROM complaints

        LEFT JOIN laboratories
            ON complaints.lab_id = laboratories.lab_id

        LEFT JOIN computers
            ON complaints.computer_id = computers.computer_id

        WHERE complaints.user_id = %s

        ORDER BY complaints.created_at DESC
    """, (session["user_id"],))

    complaints = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "student_complaint.html",
        complaints=complaints
    )


# ==========================================================
# STUDENT ADD COMPLAINT
# ==========================================================
@app.route("/student-add-complaint", methods=["GET", "POST"])
def student_add_complaint():

    if "user_id" not in session or session.get("role") != "Student":
        return redirect(url_for("user_login"))

    connection = get_connection()
    cursor = connection.cursor()

    # Get all laboratories
    cursor.execute("""
        SELECT
            lab_id,
            lab_number
        FROM laboratories
        ORDER BY lab_number
    """)

    laboratories = cursor.fetchall()

    # Get all computers
    cursor.execute("""
        SELECT
            computer_id,
            lab_id,
            pc_number
        FROM computers
        ORDER BY lab_id, pc_number
    """)

    computers = cursor.fetchall()

    if request.method == "POST":

        lab_id = request.form.get("lab_id", "").strip()
        computer_id = request.form.get("computer_id", "").strip()
        category = request.form.get("category", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "").strip()

        # Required fields
        if not lab_id or not category or not title or not description or not priority:

            cursor.close()
            connection.close()

            return render_template(
                "student_add_complaint.html",
                laboratories=laboratories,
                computers=computers,
                error="Please fill in all required fields."
            )

        # If a PC was selected, verify that it belongs to the selected laboratory
        if computer_id:

            cursor.execute("""
                SELECT computer_id
                FROM computers
                WHERE computer_id = %s
                AND lab_id = %s
            """, (computer_id, lab_id))

            valid_computer = cursor.fetchone()

            if not valid_computer:

                cursor.close()
                connection.close()

                return render_template(
                    "student_add_complaint.html",
                    laboratories=laboratories,
                    computers=computers,
                    error="The selected computer does not belong to the selected laboratory."
                )

        else:
            computer_id = None

        # Insert complaint
        cursor.execute("""
            INSERT INTO complaints
            (
                user_id,
                lab_id,
                computer_id,
                category,
                title,
                description,
                priority,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'Pending'
            )
        """, (
            session["user_id"],
            lab_id,
            computer_id,
            category,
            title,
            description,
            priority
        ))

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Complaint submitted successfully!",
            "success"
        )

        return redirect(url_for("student_complaints"))

    cursor.close()
    connection.close()

    return render_template(
        "student_add_complaint.html",
        laboratories=laboratories,
        computers=computers
    )
# ==========================================================
# START MAINTENANCE FOR COMPLAINT
# ==========================================================

@app.route("/start_maintenance/<int:complaint_id>")
def start_maintenance(complaint_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE complaints
        SET status = 'In Progress'
        WHERE complaint_id = %s
    """, (complaint_id,))

    connection.commit()

    cursor.close()
    connection.close()

    flash("Complaint moved to In Progress.", "success")

    return redirect(url_for("complaints"))
# ==========================================================
# EDIT COMPLAINT - ADMIN
# ==========================================================

@app.route("/edit_complaint/<int:complaint_id>", methods=["GET", "POST"])
def edit_complaint(complaint_id):

    if "user_id" not in session or session.get("role") != "Admin":
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    # Get complaint
    cursor.execute("""
        SELECT *
        FROM complaints
        WHERE complaint_id = %s
    """, (complaint_id,))

    complaint = cursor.fetchone()

    if not complaint:
        cursor.close()
        connection.close()

        flash("Complaint not found.", "danger")
        return redirect(url_for("complaints"))

    # Update complaint
    if request.method == "POST":

        priority = request.form.get("priority")
        status = request.form.get("status")

        cursor.execute("""
            UPDATE complaints
            SET
                priority = %s,
                status = %s,
                resolved_at =
                    CASE
                        WHEN %s IN ('Solved', 'Could Not be Resolved')
                        THEN CURRENT_TIMESTAMP
                        ELSE NULL
                    END
            WHERE complaint_id = %s
        """, (
            priority,
            status,
            status,
            complaint_id
        ))

        connection.commit()

        cursor.close()
        connection.close()

        flash("Complaint updated successfully!", "success")

        return redirect(url_for("complaints"))
    # Get laboratories
    cursor.execute("""
        SELECT lab_id, lab_number
        FROM laboratories
        ORDER BY lab_number
    """)

    laboratories = cursor.fetchall()

    # Get computers
    cursor.execute("""
        SELECT computer_id, lab_id, pc_number
        FROM computers
        ORDER BY pc_number
    """)

    computers = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "edit_complaint.html",
        complaint=complaint,
        laboratories=laboratories,
        computers=computers
    )
@app.route("/reports")
def reports():

    if "user_id" not in session or session.get("role") != "Admin":
        return redirect(url_for("login"))

    # ---------------------------------------------
    # REPORT PERIOD
    # ---------------------------------------------

    period = request.args.get("period", "this_month")

    today = datetime.now().date()

    if period == "this_month":

        start_date = today.replace(day=1)
        end_date = today
        period_title = today.strftime("%B %Y")

    elif period == "last_month":

        first_day_this_month = today.replace(day=1)
        end_date = first_day_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
        period_title = start_date.strftime("%B %Y")

    elif period == "this_week":

        start_date = today - timedelta(days=today.weekday())
        end_date = today
        period_title = (
            f"{start_date.strftime('%d %b %Y')} - "
            f"{end_date.strftime('%d %b %Y')}"
        )

    elif period == "last_week":

        this_week_start = today - timedelta(days=today.weekday())

        start_date = this_week_start - timedelta(days=7)
        end_date = this_week_start - timedelta(days=1)

        period_title = (
            f"{start_date.strftime('%d %b %Y')} - "
            f"{end_date.strftime('%d %b %Y')}"
        )

    else:

        start_date = today.replace(day=1)
        end_date = today
        period_title = today.strftime("%B %Y")


    connection = get_connection()
    cursor = connection.cursor()


    # =============================================
    # COMPLAINT REPORT
    # =============================================

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM complaints
        WHERE DATE(created_at)
        BETWEEN %s AND %s
    """, (start_date, end_date))

    complaints_received = cursor.fetchone()["total"]


    cursor.execute("""
        SELECT
            status,
            COUNT(*) AS total
        FROM complaints
        WHERE DATE(created_at)
        BETWEEN %s AND %s
        GROUP BY status
    """, (start_date, end_date))

    complaint_status_rows = cursor.fetchall()

    complaint_status = {
        "Pending": 0,
        "In Progress": 0,
        "Solved": 0,
        "Could Not be Resolved": 0
    }

    for row in complaint_status_rows:

        if row["status"] in complaint_status:
            complaint_status[row["status"]] = row["total"]


    # =============================================
    # RESOLUTION RATE
    # =============================================

    if complaints_received > 0:

        resolution_rate = round(
            (
                complaint_status["Solved"]
                / complaints_received
            ) * 100,
            1
        )

    else:

        resolution_rate = 0


    # =============================================
    # INVENTORY MOVEMENTS
    # =============================================

    cursor.execute("""
        SELECT
            inventory.inventory_id,
            inventory.item_name,
            inventory.quantity,
            inventory.unit,

            COALESCE(
                SUM(
                    CASE
                        WHEN inventory_transactions.transaction_type = 'Added'
                        THEN inventory_transactions.quantity
                        ELSE 0
                    END
                ), 0
            ) AS added,

            COALESCE(
                SUM(
                    CASE
                        WHEN inventory_transactions.transaction_type = 'Used'
                        THEN inventory_transactions.quantity
                        ELSE 0
                    END
                ), 0
            ) AS used,

            COALESCE(
                SUM(
                    CASE
                        WHEN inventory_transactions.transaction_type = 'Damaged'
                        THEN inventory_transactions.quantity
                        ELSE 0
                    END
                ), 0
            ) AS damaged,

            COALESCE(
                SUM(
                    CASE
                        WHEN inventory_transactions.transaction_type = 'Lost'
                        THEN inventory_transactions.quantity
                        ELSE 0
                    END
                ), 0
            ) AS lost,

            COALESCE(
                SUM(
                    CASE
                        WHEN inventory_transactions.transaction_type = 'Returned'
                        THEN inventory_transactions.quantity
                        ELSE 0
                    END
                ), 0
            ) AS returned

        FROM inventory

        LEFT JOIN inventory_transactions
            ON inventory.inventory_id =
               inventory_transactions.inventory_id

            AND DATE(inventory_transactions.transaction_date)
                BETWEEN %s AND %s

        GROUP BY
            inventory.inventory_id,
            inventory.item_name,
            inventory.quantity,
            inventory.unit

        ORDER BY inventory.item_name
    """, (start_date, end_date))

    inventory_reports = cursor.fetchall()


    # =============================================
    # INVENTORY ACTIVITY
    # =============================================

    cursor.execute("""
        SELECT
            inventory_transactions.transaction_id,
            inventory.item_name,
            inventory_transactions.transaction_type,
            inventory_transactions.quantity,
            inventory_transactions.reason,
            inventory_transactions.transaction_date

        FROM inventory_transactions

        INNER JOIN inventory
            ON inventory.inventory_id =
               inventory_transactions.inventory_id

        WHERE DATE(inventory_transactions.transaction_date)
              BETWEEN %s AND %s

        ORDER BY inventory_transactions.transaction_date DESC

        LIMIT 20
    """, (start_date, end_date))

    inventory_activity = cursor.fetchall()


    # =============================================
    # LOW STOCK ITEMS
    # =============================================

    cursor.execute("""
        SELECT
            item_name,
            quantity,
            minimum_stock,
            unit
        FROM inventory
        WHERE quantity <= minimum_stock
        ORDER BY quantity ASC
    """)

    low_stock_items = cursor.fetchall()


    # =============================================
    # COMPLAINT ACTIVITY
    # =============================================

    cursor.execute("""
        SELECT
            complaints.complaint_id,
            complaints.title,
            complaints.status,
            complaints.priority,
            complaints.created_at,
            complaints.resolved_at,
            laboratories.lab_number

        FROM complaints

        LEFT JOIN laboratories
            ON complaints.lab_id = laboratories.lab_id

        WHERE DATE(complaints.created_at)
              BETWEEN %s AND %s

        ORDER BY complaints.created_at DESC

        LIMIT 20
    """, (start_date, end_date))

    complaint_activity = cursor.fetchall()


    cursor.close()
    connection.close()


    # =============================================
    # FINAL REPORT
    # =============================================

    return render_template(
        "reports.html",

        period=period,
        period_title=period_title,
        start_date=start_date,
        end_date=end_date,

        complaints_received=complaints_received,
        complaint_status=complaint_status,
        resolution_rate=resolution_rate,

        inventory_reports=inventory_reports,
        inventory_activity=inventory_activity,
        low_stock_items=low_stock_items,

        complaint_activity=complaint_activity
    )
# ==========================================================
# MANAGE INVENTORY STOCK
# ==========================================================

@app.route(
    "/manage_inventory/<int:inventory_id>",
    methods=["GET", "POST"]
)
def manage_inventory(inventory_id):

    if "user_id" not in session or session.get("role") != "Admin":
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    # Get inventory item
    cursor.execute(
        """
        SELECT *
        FROM inventory
        WHERE inventory_id = %s
        """,
        (inventory_id,)
    )

    item = cursor.fetchone()

    if not item:
        cursor.close()
        connection.close()

        flash(
            "Inventory item not found.",
            "danger"
        )

        return redirect(url_for("inventory"))

    if request.method == "POST":

        transaction_type = request.form.get(
            "transaction_type",
            ""
        ).strip()

        quantity = request.form.get(
            "quantity",
            ""
        ).strip()

        reason = request.form.get(
            "reason",
            ""
        ).strip()

        # Validate quantity
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):

            cursor.close()
            connection.close()

            return render_template(
                "manage_inventory.html",
                item=item,
                error="Please enter a valid quantity."
            )

        if quantity <= 0:

            cursor.close()
            connection.close()

            return render_template(
                "manage_inventory.html",
                item=item,
                error="Quantity must be greater than zero."
            )

        if not transaction_type:

            cursor.close()
            connection.close()

            return render_template(
                "manage_inventory.html",
                item=item,
                error="Please select a stock action."
            )

        # ---------------------------------------------
        # Calculate new quantity
        # ---------------------------------------------

        current_quantity = item["quantity"] or 0

        if transaction_type in (
            "Used",
            "Damaged",
            "Lost"
        ):

            if quantity > current_quantity:

                cursor.close()
                connection.close()

                return render_template(
                    "manage_inventory.html",
                    item=item,
                    error="You cannot remove more stock than currently available."
                )

            new_quantity = current_quantity - quantity

        elif transaction_type == "Returned":

            new_quantity = current_quantity + quantity

        elif transaction_type == "Added":

            new_quantity = current_quantity + quantity

        elif transaction_type == "Adjusted":

            new_quantity = quantity

        else:

            cursor.close()
            connection.close()

            return render_template(
                "manage_inventory.html",
                item=item,
                error="Invalid stock action."
            )

        # ---------------------------------------------
        # Update inventory quantity
        # ---------------------------------------------

        cursor.execute(
            """
            UPDATE inventory
            SET quantity = %s
            WHERE inventory_id = %s
            """,
            (
                new_quantity,
                inventory_id
            )
        )

        # ---------------------------------------------
        # Record transaction
        # ---------------------------------------------

        cursor.execute(
            """
            INSERT INTO inventory_transactions
            (
                inventory_id,
                transaction_type,
                quantity,
                reason
            )
            VALUES
            (%s, %s, %s, %s)
            """,
            (
                inventory_id,
                transaction_type,
                quantity,
                reason
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash(
            "Inventory stock updated successfully!",
            "success"
        )

        return redirect(url_for("inventory"))

    cursor.close()
    connection.close()

    return render_template(
        "manage_inventory.html",
        item=item
    )
@app.route("/student-laboratories")
def student_laboratories():

    if "user_id" not in session or session.get("role") != "Student":
        return redirect(url_for("user_login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            laboratories.lab_id,
            laboratories.lab_number,
            laboratories.floor,
            laboratories.capacity,
            laboratories.status,

            COUNT(computers.computer_id) AS total_computers,

            SUM(
                CASE
                    WHEN computers.status = 'Working'
                    THEN 1
                    ELSE 0
                END
            ) AS working_computers,

            SUM(
                CASE
                    WHEN computers.status = 'Under Maintenance'
                    THEN 1
                    ELSE 0
                END
            ) AS maintenance_computers,

            SUM(
                CASE
                    WHEN computers.status = 'Out of Service'
                    THEN 1
                    ELSE 0
                END
            ) AS out_of_service_computers

        FROM laboratories

        LEFT JOIN computers
            ON laboratories.lab_id = computers.lab_id

        GROUP BY
            laboratories.lab_id,
            laboratories.lab_number,
            laboratories.floor,
            laboratories.capacity,
            laboratories.status

        ORDER BY laboratories.lab_number
    """)

    laboratories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "student_laboratories.html",
        laboratories=laboratories
    )
@app.route("/student-maintenance")
def student_maintenance():

    if "user_id" not in session or session.get("role") != "Student":
        return redirect(url_for("user_login"))

    connection = get_connection()
    cursor = connection.cursor()

    # Get all laboratories for the filter
    cursor.execute("""
        SELECT
            lab_id,
            lab_number,
            floor,
            status
        FROM laboratories
        ORDER BY lab_number
    """)

    laboratories = cursor.fetchall()

    # Get selected laboratory
    selected_lab = request.args.get("lab_id", "").strip()

    if selected_lab:
        cursor.execute("""
            SELECT
                computers.computer_id,
                computers.pc_number,
                computers.processor,
                computers.ram_gb,
                computers.storage_gb,
                computers.operating_system,
                computers.status,
                computers.purchase_date,
                computers.last_service,
                computers.remarks,
                laboratories.lab_number,
                laboratories.floor,
                laboratories.status AS lab_status
            FROM computers
            INNER JOIN laboratories
                ON computers.lab_id = laboratories.lab_id
            WHERE computers.lab_id = %s
            ORDER BY computers.pc_number
        """, (selected_lab,))

    else:
        cursor.execute("""
            SELECT
                computers.computer_id,
                computers.pc_number,
                computers.processor,
                computers.ram_gb,
                computers.storage_gb,
                computers.operating_system,
                computers.status,
                computers.purchase_date,
                computers.last_service,
                computers.remarks,
                laboratories.lab_number,
                laboratories.floor,
                laboratories.status AS lab_status
            FROM computers
            INNER JOIN laboratories
                ON computers.lab_id = laboratories.lab_id
            ORDER BY laboratories.lab_number, computers.pc_number
        """)

    computers = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "student_maintenance.html",
        computers=computers,
        laboratories=laboratories,
        selected_lab=selected_lab
    )
# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
