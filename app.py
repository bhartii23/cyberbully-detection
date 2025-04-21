from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from functools import wraps
import os
from dotenv import load_dotenv
import json
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client['cyberbullying_detection']
reports_collection = db['reports']
users_collection = db['users']

# Load stopwords and model components
with open("stopwords.txt", "r") as file:
    stopwords = file.read().splitlines()

# Load the pre-trained vectorizer and model
vectorizer = TfidfVectorizer(stop_words=stopwords, lowercase=True, vocabulary=pickle.load(open("tfidfvectoizer.pkl", "rb")))
model = pickle.load(open("LinearSVC.pkl", 'rb'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    prediction = None
    if request.method == 'POST':
        user_input = request.form['text']
        # Use transform instead of fit_transform to apply the pre-trained vocabulary
        transformed_input = vectorizer.fit_transform([user_input])
        prediction = model.predict(transformed_input)[0]
    
    return render_template('index.html', prediction=prediction)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Check if user exists in MongoDB
            user = users_collection.find_one({'email': email, 'password': password})
            
            if user:
                # Store user info in session
                session['user'] = {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'email': user['email']
                }
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'error')
        except Exception as e:
            print(f"Login error: {str(e)}")  # For debugging
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check admin credentials from environment variables
        if email == os.getenv('ADMIN_EMAIL') and password == os.getenv('ADMIN_PASSWORD'):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # Get all reports from MongoDB
    reports = list(reports_collection.find())
    return render_template('admin/dashboard.html', reports=reports)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    try:
        session.clear()
        flash('You have been successfully logged out.', 'success')
    except Exception as e:
        print(f"Logout error: {str(e)}")  # For debugging
    return redirect(url_for('login'))

@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        bully_name = request.form.get('bully_name', '')
        platform = request.form.get('platform')
        incident_date = request.form.get('incident_date')
        report_text = request.form.get('report')
        evidence = request.form.get('evidence', '')
        severity = request.form.get('severity')
        
        # Validate required fields
        if not all([platform, incident_date, report_text, severity]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('report'))
        
        # Create report object
        report_data = {
            'user_id': session['user']['id'],
            'user_name': session['user']['name'],
            'user_email': session['user']['email'],
            'bully_name': bully_name,
            'platform': platform,
            'incident_date': incident_date,
            'report': report_text,
            'evidence': evidence,
            'severity': severity,
            'submission_date': datetime.now(),
            'status': 'pending'
        }
        
        # Store report in MongoDB
        reports_collection.insert_one(report_data)
        
        flash('Report submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('report.html', user=session['user'])

@app.route('/admin/report/<report_id>/review', methods=['POST'])
def review_report(report_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # Update report status in MongoDB
    reports_collection.update_one(
        {'_id': ObjectId(report_id)},
        {'$set': {'status': 'reviewed'}}
    )
    
    flash('Report marked as reviewed.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/report/<report_id>/resolve', methods=['POST'])
def resolve_report(report_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # Update report status in MongoDB
    reports_collection.update_one(
        {'_id': ObjectId(report_id)},
        {'$set': {'status': 'resolved'}}
    )
    
    flash('Report marked as resolved.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/report/<report_id>/delete', methods=['POST'])
def delete_report(report_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        # Delete report from MongoDB
        result = reports_collection.delete_one({'_id': ObjectId(report_id)})
        
        if result.deleted_count > 0:
            flash('Report deleted successfully.', 'success')
        else:
            flash('Report not found or already deleted.', 'error')
            
    except Exception as e:
        print(f"Delete error: {str(e)}")  # For debugging
        flash('An error occurred while deleting the report.', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/contacts')
def contacts():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('contacts.html', user=session['user'])

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').lower()
    
    # Simple response logic
    if 'hello' in user_message or 'hi' in user_message:
        response = "Hello! How can I help you today?"
    elif 'cyberbullying' in user_message:
        response = "Cyberbullying is bullying that takes place over digital devices. It can include sending, posting, or sharing negative, harmful, false, or mean content about someone else."
    elif 'report' in user_message:
        response = "To report cyberbullying, please use our report form. You can find it in the dashboard or click the 'Report' button when cyberbullying is detected."
    elif 'help' in user_message:
        response = "I can help you understand cyberbullying, guide you through the reporting process, or provide information about prevention. What would you like to know?"
    else:
        response = "I'm here to help with cyberbullying-related questions. Could you please rephrase your question?"
    
    return jsonify({'response': response})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        if users_collection.find_one({'email': email}):
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        # Create new user in MongoDB
        user_data = {
            'name': name,
            'email': email,
            'password': password,
            'created_at': datetime.now()
        }
        users_collection.insert_one(user_data)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
