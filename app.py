from flask import Flask,render_template,flash,request,redirect,session,url_for,send_from_directory
import mysql.connector
import os
from datetime import date
app = Flask(__name__)
app.secret_key='your_secrete_key'

def get_dbconnection():
    conn=mysql.connector.connect(
        host='localhost',
        user='root',
        port='3307',
        password='',
        database='student'
    )
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/About")
def About():
    return render_template("About.html")

@app.route("/Contact")
def Contact():
    return render_template("Contact.html")

@app.route("/Menu")
def Menu():
    return render_template("Menu.html")

@app.route("/Registration",methods=["GET","POST"])
def Registration():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        mobile=request.form['mobile']
        password=request.form['password']
        
        conn=get_dbconnection()
        cursor=conn.cursor()
        cursor.execute('insert into registration(name,email,mobile_no,password) values (%s,%s,%s,%s)',(name,email,mobile,password))
        conn.commit()
        conn.close()
        
        flash('Registration details added successfully!','success')
        return redirect("/Registration")
    
    return render_template("Registration.html")

@app.route("/Login", methods=["GET", "POST"])
def Login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = None
        cursor = None

        try:
            conn = get_dbconnection()

            cursor = conn.cursor(dictionary=True, buffered=True)

            cursor.execute(
                "SELECT * FROM registration WHERE Email=%s",
                (email,)
            )

            user = cursor.fetchone()

            if user:

                if user["Password"] == password:

                    session["user"] = user["Email"]

                    flash("Login Successful!", "success")

                    return redirect("/Customerdashboard")

                else:

                    flash("Incorrect Password!", "danger")

            else:

                flash("Email not found!", "danger")

        except Exception as e:

            print("LOGIN ERROR:", e)

            flash("Login error: " + str(e), "danger")

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()

    return render_template("Login.html")

@app.route("/Logout")
def Logout():
    session.pop("user",None)
    flash("Logged out successfully!","success")
    return redirect("/")

@app.route("/AdminLogin",methods=["GET","POST"])
def AdminLogin():
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]
        conn = get_dbconnection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM admin WHERE Email=%s",
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            if user["Password"] == password:
                session["admin"] = user["Email"]    
                flash("Login Successful!", "success")
                return redirect("/Dashboard")
            else:
                flash("Incorrect Password!", "danger")
        else:
            flash("Email not found!", "danger")
    return render_template("AdminLogin.html")


@app.route("/Dashboard", methods=["GET", "POST"])
def Dashboard():

    conn = get_dbconnection()
    cursor = conn.cursor(dictionary=True)

    # =====================================================
    # SAVE / UPDATE MENU
    # =====================================================

    if request.method == "POST":

        menu_id = request.form.get("menu_id")

        category = request.form["category"]
        name = request.form["name"]
        price = request.form["price"]

        image = request.files.get("image")

        upload_folder = os.path.join(
            app.root_path,
            "static",
            "uploads"
        )

        os.makedirs(upload_folder, exist_ok=True)


        # =================================================
        # UPDATE EXISTING MENU
        # =================================================

        if menu_id:

            # Get old menu
            cursor.execute(
                """
                SELECT *
                FROM menutable
                WHERE id = %s
                """,
                (menu_id,)
            )

            old_menu = cursor.fetchone()

            if old_menu is None:

                cursor.close()
                conn.close()

                flash(
                    "Menu item not found!",
                    "danger"
                )

                return redirect(url_for("Dashboard"))


            # ---------------------------------------------
            # New image selected
            # ---------------------------------------------

            if image and image.filename != "":

                filename = image.filename

                image_path = os.path.join(
                    upload_folder,
                    filename
                )

                image.save(image_path)

                db_image_path = "uploads/" + filename


                cursor.execute(
                    """
                    UPDATE menutable
                    SET
                        category = %s,
                        name = %s,
                        price = %s,
                        image = %s
                    WHERE id = %s
                    """,
                    (
                        category,
                        name,
                        price,
                        db_image_path,
                        menu_id
                    )
                )

            else:

                # -----------------------------------------
                # Keep old image
                # -----------------------------------------

                cursor.execute(
                    """
                    UPDATE menutable
                    SET
                        category = %s,
                        name = %s,
                        price = %s
                    WHERE id = %s
                    """,
                    (
                        category,
                        name,
                        price,
                        menu_id
                    )
                )


            conn.commit()

            cursor.close()
            conn.close()

            flash(
                "Menu item updated successfully!",
                "success"
            )

            return redirect(url_for("Dashboard"))


        # =================================================
        # INSERT NEW MENU
        # =================================================

        else:

            if image is None or image.filename == "":

                cursor.close()
                conn.close()

                flash(
                    "Please select an image!",
                    "danger"
                )

                return redirect(url_for("Dashboard"))


            filename = image.filename

            image_path = os.path.join(
                upload_folder,
                filename
            )

            image.save(image_path)

            db_image_path = "uploads/" + filename


            cursor.execute(
                """
                INSERT INTO menutable
                (
                    category,
                    name,
                    price,
                    image
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    category,
                    name,
                    price,
                    db_image_path
                )
            )

            conn.commit()

            cursor.close()
            conn.close()

            flash(
                "Menu item saved successfully!",
                "success"
            )

            return redirect(url_for("Dashboard"))


    # =====================================================
    # GET MENUS
    # =====================================================

    cursor.execute(
        """
        SELECT
            id,
            category,
            name,
            price,
            image
        FROM menutable
        ORDER BY id DESC
        """
    )

    menus = cursor.fetchall()


    # =====================================================
    # CHECK IF EDITING A MENU
    # =====================================================

    edit_id = request.args.get("edit")

    edit_menu = None

    if edit_id:

        cursor.execute(
            """
            SELECT
                id,
                category,
                name,
                price,
                image
            FROM menutable
            WHERE id = %s
            """,
            (edit_id,)
        )

        edit_menu = cursor.fetchone()


    cursor.close()
    conn.close()


    return render_template(
        "Dashboard.html",
        menus=menus,
        edit_menu=edit_menu
    )


# =========================================================
# DELETE MENU
# =========================================================

@app.route("/delete_menu/<int:id>", methods=["POST"])
def delete_menu(id):

    conn = get_dbconnection()
    cursor = conn.cursor(dictionary=True)


    # Get image before deleting row
    cursor.execute(
        """
        SELECT image
        FROM menutable
        WHERE id = %s
        """,
        (id,)
    )

    menu = cursor.fetchone()


    if menu is None:

        cursor.close()
        conn.close()

        flash(
            "Menu item not found!",
            "danger"
        )

        return redirect(url_for("Dashboard"))


    # =====================================================
    # DELETE DATABASE ROW
    # =====================================================

    cursor.execute(
        """
        DELETE FROM menutable
        WHERE id = %s
        """,
        (id,)
    )

    conn.commit()


    # =====================================================
    # DELETE IMAGE
    # =====================================================

    if menu["image"]:

        image_path = os.path.join(
            app.root_path,
            "static",
            menu["image"]
        )

        if os.path.exists(image_path):

            os.remove(image_path)


    cursor.close()
    conn.close()


    flash(
        "Menu item deleted successfully!",
        "success"
    )

    return redirect(url_for("Dashboard"))

@app.route("/vieworder")
def vieworder():

    conn = get_dbconnection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            Id,
            Name,
            Price,
            Quantity,
            Total,
            Date
        FROM orderedmenu
        ORDER BY Id DESC
        """
    )

    orders = cursor.fetchall()

    cursor.close()

    conn.close()

    return render_template(
        "ViewOrder.html",
        orders=orders
    )

@app.route("/Customerdashboard")
def Customerdashboard():

    conn = get_dbconnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM menutable ORDER BY id")

    menu_items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "Customerdashboard.html",
        menu_items=menu_items
    )
    
import os
from flask import send_from_directory

@app.route("/coffee-images/<filename>")
def coffee_images(filename):
    upload_folder = os.path.join(
        app.root_path,
        "static",
        "uploads"
    )

    return send_from_directory(
        upload_folder,
        filename
    )

@app.route("/order", methods=["GET", "POST"])
def order():

    conn = get_dbconnection()
    cursor = conn.cursor(dictionary=True)

    # -----------------------------
    # SHOW ORDER FORM
    # -----------------------------
    if request.method == "GET":

        menu_id = request.args.get("menu_id")

        cursor.execute(
            "SELECT * FROM menutable WHERE id = %s",
            (menu_id,)
        )

        item = cursor.fetchone()

        cursor.close()
        conn.close()

        if not item:
            flash("Menu item not found!", "danger")
            return redirect("/Customerdashboard")

        return render_template(
            "Order.html",
            item=item
        )

    # -----------------------------
    # SAVE ORDER
    # -----------------------------
    if request.method == "POST":

        name = request.form["name"]
        price = int(request.form["price"])
        quantity = int(request.form["quantity"])

        total = price * quantity

        order_date = date.today()

        cursor.execute(
            """
            INSERT INTO orderedmenu
            (Name, Price, Quantity, Total, Date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                name,
                price,
                quantity,
                total,
                order_date
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Order placed successfully!", "success")

        return redirect("/vieworder")
    
@app.route("/billing", methods=["POST"])
def billing():

    name = request.form.get("name")
    price = request.form.get("price")
    quantity = request.form.get("quantity")

    if not name or not price or not quantity:
        flash("Invalid order details!", "danger")
        return redirect("/Customerdashboard")

    price = int(price)
    quantity = int(quantity)

    total = price * quantity

    return render_template(
        "Billing.html",
        name=name,
        price=price,
        quantity=quantity,
        total=total
    )
    
@app.route("/confirm-order", methods=["POST"])
def confirm_order():

    name = request.form["name"]
    price = int(request.form["price"])
    quantity = int(request.form["quantity"])
    total = int(request.form["total"])
    payment_method = request.form["payment_method"]

    order_date = date.today()

    conn = get_dbconnection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO orderedmenu
        (Name, Price, Quantity, Total, Date)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            name,
            price,
            quantity,
            total,
            order_date
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash(
        "Order placed successfully using " + payment_method + "!",
        "success"
    )

    return redirect("/Customerdashboard")
@app.route("/feedback", methods=["GET", "POST"])
def feedback():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        rating = request.form["rating"]
        message = request.form["message"]

        conn = get_dbconnection()
        cursor = conn.cursor()

        try:

            sql = """
                INSERT INTO feedback
                (Name, Email, Rating, Message)
                VALUES (%s, %s, %s, %s)
            """

            values = (
                name,
                email,
                int(rating),
                message
            )

            cursor.execute(sql, values)

            conn.commit()

            print("Feedback inserted:", cursor.rowcount)

            flash(
                "Thank you! Your feedback has been submitted successfully.",
                "success"
            )

        except Exception as e:

            conn.rollback()

            print("FEEDBACK INSERT ERROR:", e)

            flash(
                "Feedback error: " + str(e),
                "danger"
            )

        finally:

            cursor.close()
            conn.close()

        return redirect("/feedback")

    return render_template("feedback.html")
@app.route("/FeedbackRepository")
def FeedbackRepository():

    conn = get_dbconnection()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("SELECT * FROM feedback ORDER BY Id DESC")

        feedbacks = cursor.fetchall()

        print("Feedbacks retrieved:")
        print(feedbacks)

    except Exception as e:

        print("FEEDBACK RETRIEVE ERROR:", e)

        feedbacks = []

    finally:

        cursor.close()
        conn.close()

    return render_template(
        "FeedbackRepository.html",
        feedbacks=feedbacks
    )
        
if __name__ == "__main__":
    app.run(debug=True)