from flask import Flask, render_template, redirect, request, session, url_for, jsonify
import pyrebase
from datetime import datetime



app = Flask(__name__)
app.secret_key = 'deeps'
count = 0

firebaseConfig = {
  "apiKey": "AIzaSyAHx1SzHjB95PfWuwF5qkxLpcswDpq2-Jo",
  "authDomain": "fitbyit2024.firebaseapp.com",
  "projectId": "fitbyit2024",
  "storageBucket": "fitbyit2024.appspot.com",
  "messagingSenderId": "292945432667",
  "appId": "1:292945432667:web:f966259207ea3a7789ef7e",
  "databaseURL": "https://fitbyit2024-default-rtdb.firebaseio.com/"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()


## SignUp Logic
def create_user(email, password):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        session['user_id'] = user['idToken']
        return user
    except Exception as e:
        return None 

## Sign Up Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = create_user(email, password)
        if user:
            return redirect('/verify')
        else:
            return render_template('signup.html', error= "Something went wrong. Try Again !!")
    return render_template('signup.html')

## Verify Up Route
@app.route('/verify', methods=['GET', 'POST'])
def verification():
    try:
        user_id = session.get('user_id')
        getinfo = auth.get_account_info(user_id)
        emailcheck = getinfo["users"][0]["emailVerified"]
        email = getinfo["users"][0]["email"]
        if emailcheck==True:
            return redirect("/")
        else:
            auth.send_email_verification(user_id)
        return render_template("verify.html", email = email)
    except:
        return render_template("404.html")


## Login Logic
def verify_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        session['user_id'] = user['idToken']
        return user
    except Exception as e:
        return False
    
# Home Route 
@app.route('/')
def home():
    user_id = session.get('user_id')
    if user_id:
        try:
            user_info = auth.get_account_info(user_id)
            user_ref = f'users/{user_info["users"][0]["localId"]}'
            user_data = db.child(user_ref).get().val()
            if user_data:
                count = user_data.get('count', 0)
                date = user_data.get('date', 'NA')
                return render_template('home.html', user_info = user_info, countdata = count, date= date)
            else:
                return render_template('home.html', user_info = user_info, countdata = "NA", date= "NA")
        except Exception as e:
            session.pop('user_id', None)
            return render_template('login.html')
    return redirect("/login")


## Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not session.get('user_id'):
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = verify_user(email, password)
            if user:
                return redirect('/verify')
            else:
                return render_template('login.html', error="Invalid Email or Password")
        return render_template('login.html')
    return redirect("/")

## Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

## Forget Password Route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            auth.send_password_reset_email(email)
            return render_template("login.html", error = "Password reset email sent.")
        except Exception as e:
            return render_template("forgot_password.html", error = "Failed to send email.")
    return render_template('forgot_password.html')
    
## 404 Route
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('404.html'), 500

@app.route('/count', methods=['GET', 'POST'])
def startCount():
    return render_template('counter.html')



def update_pushup_count_in_firebase(localId, count):
    today_date = datetime.now().strftime('%d %b %y')
    user_ref = f'users/{localId}'
    user_data = {'count': count, 'date': today_date}
    db.child(user_ref).set(user_data) 

@app.route('/stopcount', methods=['POST', "GET"])
def stopcount():
    global count
    try:
        data = request.get_json()
        count = data['count']
        user_id = session.get('user_id')
        user_info = auth.get_account_info(user_id)
        localId = user_info["users"][0]["localId"]
        update_pushup_count_in_firebase(localId, round(count))
        count = 0
        response_data = {'status': 'success'}
        return jsonify(response_data)
    except:
        return jsonify({'status': 'error'})
    

if __name__ == '__main__':
    app.run()