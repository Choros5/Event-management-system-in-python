import mysql.connector
import sys
import datetime
from mysql.connector import Error
from flask import Flask, request, jsonify, render_template, redirect, url_for
from random import randint

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def renderLoginPage():
    events = runQuery("SELECT * FROM events")
    branch = runQuery("SELECT * FROM branch")
    
    if request.method == 'POST':
        name = request.form['FirstName'] + " " + request.form['LastName']
        mobile = request.form['MobileNumber']
        branch_id = request.form['Branch']
        event = request.form['Event']
        email = request.form['Email']

        if len(mobile) != 10:
            return render_template('loginfail.html', errors=["Invalid Mobile Number!"])

        if email[-4:] != '.com':
            return render_template('loginfail.html', errors=["Invalid Email!"])

        if len(runQuery(f"SELECT * FROM participants WHERE event_id={event} AND mobile={mobile}")) > 0:
            return render_template('loginfail.html', errors=["Student already Registered for the Event!"])

        if runQuery(f"SELECT COUNT(*) FROM participants WHERE event_id={event}") >= runQuery(f"SELECT participants FROM events WHERE event_id={event}"):
            return render_template('loginfail.html', errors=["Participants count fullfilled Already!"])

        runQuery(f"INSERT INTO participants(event_id, fullname, email, mobile, college, branch_id) VALUES({event}, \"{name}\", \"{email}\", \"{mobile}\", \"COEP\", \"{branch_id}\");")

        return render_template('index.html', events=events, branchs=branch, errors=["Successfully Registered!"])

    return render_template('index.html', events=events, branchs=branch)

@app.route('/loginfail', methods=['GET'])
def renderLoginFail():
    return render_template('loginfail.html')

@app.route('/admin', methods=['GET', 'POST'])
def renderAdmin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        credentials = runQuery("SELECT * FROM admin")
        for user in credentials:
            if username == user[0] and password == user[1]:
                return redirect('/eventType')

        return render_template('admin.html', errors=["Wrong Username/Password"])

    return render_template('admin.html')

@app.route('/eventType', methods=['GET', 'POST'])
def getEvents():
    event_types = runQuery("""
        SELECT *, (SELECT COUNT(*) FROM participants AS P WHERE T.type_id IN 
        (SELECT type_id FROM events AS E WHERE E.event_id = P.event_id)) AS COUNT 
        FROM event_type AS T;
    """)

    events = runQuery("""
        SELECT event_id, event_title, (SELECT COUNT(*) FROM participants AS P WHERE P.event_id = E.event_id) AS count 
        FROM events AS E;
    """)

    types = runQuery("SELECT * FROM event_type;")
    location = runQuery("SELECT * FROM location")

    if request.method == 'POST':
        try:
            name = request.form["newEvent"]
            fee = request.form["Fee"]
            participants = request.form["maxP"]
            event_type = request.form["EventType"]
            event_location = request.form["EventLocation"]
            date = request.form['Date']
            
            runQuery(f"""
                INSERT INTO events(event_title, event_price, participants, type_id, location_id, date) 
                VALUES("{name}", {fee}, {participants}, {event_type}, {event_location}, '{date}');
            """)
        except:
            event_id = request.form["EventId"]
            runQuery(f"DELETE FROM events WHERE event_id={event_id}")

    return render_template('events.html', events=events, eventTypes=event_types, types=types, locations=location)

@app.route('/eventinfo')
def renderEventInfo():
    events = runQuery("""
        SELECT *, (SELECT COUNT(*) FROM participants AS P WHERE P.event_id = E.event_id) AS count 
        FROM events AS E 
        LEFT JOIN event_type USING(type_id) 
        LEFT JOIN location USING(location_id);
    """)

    return render_template('events_info.html', events=events)

@app.route('/participants', methods=['GET', 'POST'])
def renderParticipants():
    events = runQuery("SELECT * FROM events;")

    if request.method == 'POST':
        event = request.form['Event']
        participants = runQuery(f"SELECT p_id, fullname, mobile, email FROM participants WHERE event_id={event}")
        return render_template('participants.html', events=events, participants=participants)

    return render_template('participants.html', events=events)

def runQuery(query):
    try:
        db = mysql.connector.connect(
            host='localhost',
            database='event_mgmt',
            user='root',
            password='password'
        )

        if db.is_connected():
            print("Connected to MySQL, running query: ", query)
            cursor = db.cursor(buffered=True)
            cursor.execute(query)
            db.commit()
            
            try:
                res = cursor.fetchall()
            except Exception as e:
                print("Query returned nothing: ", e)
                return []
            
            return res

    except Exception as e:
        print(e)
        return []

    db.close()
    print("Couldn't connect to MySQL")
    return None

if __name__ == "__main__":
    app.run()
