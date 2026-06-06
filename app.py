import os
import os
import pathlib
import sqlite3
from datetime import datetime

import cachecontrol
import google
import requests
from flask import Flask, redirect, request, make_response, session
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

app = Flask("School system Version: 0.0.1")
app.secret_key = "your-secret-key-here"
con = sqlite3.connect("students.sqlite", check_same_thread=False)
app.config.update(
    SESSION_COOKIE_HTTPONLY=False,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

cur = con.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username CHAR(100),
        name CHAR(100),
        password CHAR(100),
        email CHAR(150),
        role CHAR(150)
    );
""")

con.commit()


#OAUTH
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = "246680970542-e2e633gvfr08uo9ajdh14dgks016ilhf.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(client_secrets_file,
                               scopes=["https://www.googleapis.com/auth/userinfo.profile"], redirect_uri="http://localhost:8080/callback")
@app.route("/users")
def users():


    url = "https://timeapi.io/api/Time/current/zone?timeZone=Europe/Copenhagen"
    response = requests.get(url)
    data = response.json()
    dt = datetime.fromisoformat(data["dateTime"])
    time_only = dt.strftime("%H:%M:%S")
    resp_html = (
                "<html><head><meta http-equiv='refresh' content='60'><title>XSS</title></head><body>" + " <h1>Current time is :" + time_only + "</h1>")

    user_ = request.args.get('username')
    cur.execute("SELECT * FROM users where username = '"+user_+"' and role ='Administrator'")
    rows = cur.fetchone()
    if rows:
       session["username"] = user_

       cur.execute("SELECT * FROM users")
       rows = cur.fetchall()

       result = resp_html + "<ul> <li> <b>username &nbsp name &nbsp password &nbsp email &nbsp role</b></li>"
       for row in rows:
           result += "<li>"+ str(row[0]) + "&nbsp" + str(row[1]) + "&nbsp" + str(row[2]) + "&nbsp" + str(row[3]) + "&nbsp" + "</li>"
       result += "<li><h1><a href='/logout'>Logout</a></h1></li></ul>"
       resp = make_response(result)
       resp.headers["Refresh"] = "60"
       return resp
    else:
       return "<h1>Permission Denied for " + user_ + " &nbsp; <a href='/logout'>Logout</a></h1>"

@app.route("/register")
def register():
   if "username" in session:
       return redirect("/users?username=" + session["username"])
   user_ = request.args.get('username')
   pass_ = request.args.get('password')
   name_ = request.args.get('fullname')
   email_ = request.args.get('email')
   role_ = request.args.get('roles')

   cur.execute("INSERT INTO users (username, name, password, email, role) VALUES (?, ?, ?, ?, ?)", (user_, name_, pass_, email_, role_))
   con.commit()
   return ("<html><head><title>Register</title><body>"+
           " Registration success for "+ user_+ " An email is sent to your email account. <a href='/login'> Login</a></body></html>")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/login")
def login():
    if "username" in session:
        return redirect("/users?username="+session["username"])
    return ("<html><head><title>Login</title><body>" +
            " <h1> Please Login </h1 >" +
            " <form action='/users' method='get'>" +
            " <label>Username:</label><br> "+
            " <input type='text' name='username' id = 'u'><br><br>"+
            " <label>Password:</label><br>"+
            " <input type='password' name='password'><br><br>"+
            " <button type='submit'>Login</button>"+
            " </form><body>")


@app.route("/")
def index():
    if "username" in session:
        return redirect("/users?username="+session["username"])
    resp_html = ("<html><head><title>XSS</title></head><body>"+
            " <h1>Please Register:</h1>" +
            " <form action='/register' method='get'>"+
            " <div id = 'div'>" +
            " <label>Username:</label><br> "+
            " <input type='text' name='username'><br><br>"+
            " <label>E-mail:</label><br> " +
            " <input type='text' name='email' id = 'e'><br><br>" +
            " <label>Full name:</label><br> " +
            " <input type='text' name='fullname' id = 'f'><br><br>" +
            " <label>Role:</label><br> " +
            " <select id = 'roles' name='roles'>"+
            " <option value='Administrator'>Administrator </option>" +
            " <option value='Student'> Student </option> <select>"
            " <br><br>" +
            " <label>Password:</label><br>"+
            " <input type='password' name='password' id ='pwd'>" +
            " <br><button type='submit'> Register </button>" +
            " <br><br></form>"+
            " <h1><a href='/login'>Please Login</a></h1>"+
            " <h1><a href='/loginOAuth'>Login with Google</a></h1>" +
            " <body>")

    resp = make_response(resp_html)
    return resp

@app.route("/loginOAuth")
def loginOAuth():
   if "username" in session:
       return redirect("/users?username=" + session["username"])
   authorization_url, state = flow.authorization_url()
   return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    token_request.credentials = credentials

    id_info = id_token.verify_oauth2_token(id_token=credentials.id_token,request=token_request, audience=GOOGLE_CLIENT_ID)
    #login as student per default
    cur.execute("INSERT INTO users (username, name, password, email, role) VALUES (?, ?, ?, ?, ?)",
               (id_info['name'], id_info['name'], id_info['name'], id_info['name'], 'Administrator'))
    con.commit()
    return  redirect("/users?username="+id_info['name'])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)







