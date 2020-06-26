import MySQLdb
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)
app.secret_key = "super secret key"

# Configure db
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)

global_user_name = 'julia'


# 这里要改成github账户登录的代码
@app.route('/', methods=['GET', 'POST'])
def index():
    # display the current flight
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM flight")
    if resultValue > 0:
        flightDetails = cur.fetchall()

    if request.method == "POST":
        return redirect(url_for('search'))
    return render_template('home/index.html', flightDetails=flightDetails)


@app.route('/order')
def users():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM customers")
    if resultValue > 0:
        userDetails = cur.fetchall()
        return render_template('user.html', userDetails=userDetails)


# 还没有处理异常输入情况
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        requestflight = request.form
        da = requestflight['出发城市']
        aa = requestflight['到达城市']
        dd = requestflight['出发日期']

        curs = mysql.connection.cursor()
        result = curs.execute("SELECT * FROM flight_view WHERE 出发城市=%s and 到达城市=%s and 出发日期=%s", (da, aa, dd))
        if result > 0:
            data = curs.fetchall()

        mysql.connection.commit()
        curs.close()
        return render_template("home/search.html", data=data)
    return render_template("home/search.html")


# 注册
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template("home/register.html")
    else:
        name = request.form['name']
        type = request.form['type']
        password = request.form['password'].encode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO passenger (name, type, password) VALUES (%s, %s,%s)", (name, type, password))
        mysql.connection.commit()
        # session['name'] = request.form['name']

        return redirect(url_for('index'))


# 登录
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password'].encode('utf-8')

        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute("SELECT * FROM passenger WHERE name=%s", (name,))
        user = curl.fetchone()
        curl.close()

        if len(user) > 0:
            if str(user["password"].encode('utf-8')) == str(password):
                session['name'] = user['name']
                global global_user_name
                global_user_name = name
                return redirect(url_for('search_login'))
            else:
                return "Error password and email not match"
        else:
            return "Error user not found"
    else:
        return render_template("home/login.html")


@app.route("/dashboard")
def dashboard():
    global global_user_name
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT passenger_id FROM passenger WHERE name = %s", [global_user_name])
    if result > 0:
        user_id = cur.fetchone()
    else:
        return '登陆异常'

    resultValue = cur.execute("SELECT ticket_id, seat_type, actual_fare, ticket.flight_id, departure_airport, destination_airport, departure_time,\
                arrival_time  FROM ticket, flight WHERE passenger_id = %s and flight.flight_id = ticket.flight_id",
                              user_id)

    if resultValue > 0:
        tickets = cur.fetchall()
    else:
        return render_template("home/dashboard.html")
    return render_template("home/dashboard.html", tickets=tickets)


@app.route('/search_login', methods=['GET', 'POST'])
def search_login():
    if request.method == "POST":
        requestflight = request.form
        da = requestflight['出发城市']
        aa = requestflight['到达城市']
        dd = requestflight['出发日期']

        curs = mysql.connection.cursor()
        result = curs.execute("SELECT * FROM flight_view WHERE 出发城市=%s and 到达城市=%s and 出发日期=%s", (da, aa, dd))
        if result > 0:
            data = curs.fetchall()

        mysql.connection.commit()
        curs.close()
        return render_template("home/search_login.html", data=data)
    return render_template("home/search_login.html")


@app.route('/logout')
def logout():
    global global_user_name
    global_user_name = 'julia'
    return redirect(url_for('index'))


@app.route('/insert_data/<string:seat_type>/<string:flight_id>')
def insert_data(seat_type, flight_id):
    global global_user_name
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT passenger_id FROM passenger WHERE name = %s", [global_user_name])
    if result > 0:
        user_id = cur.fetchone()
    else:
        return '登陆异常'

    result = cur.execute("SELECT buytickets_discount FROM price_info, passenger WHERE passenger_id = %s \
                         and price_info.passenger_type = passenger.type", user_id)
    if result > 0:
        discount = cur.fetchone()[0]
    else:
        return 'cannot fetchone desired discount'

    result = cur.execute("SELECT ticket_price FROM ticket_info WHERE flight_id = %s and seat_type= %s",
                         (flight_id, seat_type))
    if result > 0:
        ticket_price = cur.fetchone()[0]
    else:
        return 'cannot fetchone desired ticket_price'

    cur.execute("INSERT INTO ticket (passenger_id, flight_id, seat_type, actual_fare) \
                VALUES(%s, %s,%s,%s)", (user_id, flight_id, seat_type, ticket_price * discount))

    mysql.connection.commit()
    return redirect(url_for('search_login'))


@app.route('/delete/<string:id_data>', methods=['GET', 'POST'])
def delete(id_data):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM ticket WHERE ticket_id = %s", [id_data])
    mysql.connection.commit()
    return redirect(url_for('dashboard'))


@app.route('/manager_login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password'].encode('utf-8')

        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute("SELECT * FROM manager WHERE name=%s", (name,))
        user = curl.fetchone()
        curl.close()

        if len(user) > 0:
            if str(user["password"].encode('utf-8')) == str(password):
                return redirect(url_for('manager_board'))
            else:
                return "Error password and email not match"
        else:
            return "Error user not found"
    else:
        return render_template("manage/manager_login.html")


@app.route('/manager_board', methods=['GET', 'POST'])
def manager_board():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM flight")
    if resultValue > 0:
        flightDetails = cur.fetchall()

    return render_template('manage/manager_board.html', flightDetails=flightDetails)


@app.route('/update_flight', methods=['GET', 'POST'])
def update_flight():
    if request.method == 'POST':
        flight_id = request.form['飞机编号']
        dd = request.form['出发机场']
        da = request.form['到达机场']
        dt = request.form['出发时间']
        at = request.form['到达时间']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE flight \
               SET departure_airport=%s, destination_airport=%s, departure_time=%s, \
               arrival_time=%s WHERE flight_id=%s", (dd, da, dt, at, flight_id))
        mysql.connection.commit()
    return redirect(url_for('manager_board'))


@app.route('/delete_flight/<string:flight_id>', methods=['GET', 'POST'])
def delete_flight(flight_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM flight WHERE flight_id = %s", [flight_id])
    mysql.connection.commit()
    return redirect(url_for('manager_board'))


if __name__ == '__main__':
    app.debug = True
    app.run()
