from flask import Flask, render_template, request, redirect, url_for, session

import json
import logging
import os



# Configure logging
logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ensure session functionality


# Load data
def load_data(file):
	file_path = f"data/{file}"
	if not os.path.exists(file_path):
		with open(file_path, "w") as f:
			json.dump([], f)

	try:
		with open(file_path, "r") as f:
			return json.load(f)
	except json.JSONDecodeError:
		logging.error(f"Error loading {file}: Resetting to empty array")
		with open(file_path, "w") as f:
			json.dump([], f)
		return []


# Save data
def save_data(file, data):
	file_path = f"data/{file}"
	with open(file_path, "w") as f:
		json.dump(data, f, indent=4)


# Routes
@app.route('/')
def index():
	return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		users = load_data('users.json')
		name = request.form['name']
		email = request.form['email']
		password = request.form['password']
		if any(u['email'] == email for u in users):
			return "Error: Email already registered."
		users.append({"id": len(users) + 1, "name": name, "email": email, "password": password})
		save_data('users.json', users)
		return redirect(url_for('login'))
	return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		users = load_data('users.json')
		email = request.form['email']
		password = request.form['password']
		user = next((u for u in users if u['email'] == email and u['password'] == password), None)
		if user:
			session['user_id'] = user['id']
			return redirect(url_for('dashboard'))
		return "Invalid credentials."
	return render_template('login.html')


@app.route('/track', methods=['GET', 'POST'])
def track():
	tracking_result = None
	if request.method == 'POST':
		shipment_id = request.form['shipment_id']
		shipments = load_data('shipments.json')
		tracking_result = next((s for s in shipments if s['id'] == shipment_id), None)
	return render_template('track.html', tracking_result=tracking_result)


@app.route('/book', methods=['GET', 'POST'])
def book():
	if request.method == 'POST':
		bookings = load_data('bookings.json')
		shipment_id = request.form['shipment_id']
		user_id = session.get('user_id')
		if not user_id:
			return redirect(url_for('login'))
		bookings.append(
			{"id": len(bookings) + 1, "user_id": user_id, "shipment_id": shipment_id, "details": "Booking details"})
		save_data('bookings.json', bookings)
		return "Booking created successfully!"
	return render_template('book.html')


@app.route('/dashboard')
def dashboard():
	user_id = session.get('user_id')
	if not user_id:
		return redirect(url_for('login'))
	users = load_data('users.json')
	user = next((u for u in users if u['id'] == user_id), None)
	bookings = load_data('bookings.json')
	return render_template('dashboard.html', user=user, bookings=bookings)


@app.route('/logout')
def logout():
	session.pop('user_id', None)
	return redirect(url_for('index'))



@app.route('/test-static')
def test_static():
    return url_for('static', filename='css/styles.css')


if __name__ == '__main__':
	if not os.path.exists("data"):
		os.makedirs("data")
	app.run(debug=True)

