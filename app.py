from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)

# Configure db
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)


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


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        requestflight = request.form
        da = requestflight['出发机场']
        aa = requestflight['到达机场']
        dd = requestflight['出发日期']
        ad = requestflight['到达日期']

        curs = mysql.connection.cursor()
        result = curs.execute("SELECT * FROM flight WHERE departure_airport = %s and destination_airport = %s \
                                     and departure_date = %s and arrival_date = %s", (da, aa, dd, ad))
        if result > 0:
            data = curs.fetchall()

        mysql.connection.commit()
        curs.close()
        return render_template("home/search.html", data=data)
    return render_template("home/search.html")


if __name__ == '__main__':
    app.debug = True
    app.run()
