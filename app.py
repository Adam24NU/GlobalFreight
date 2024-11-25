from flask import Flask, render_template, request, redirect, url_for, session, jsonify

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

        # Ensure the user is logged in
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        # Gather form data
        sender_name = request.form['sender_name']
        sender_email = request.form['sender_email']
        sender_phone = request.form['sender_phone']
        pickup_address = request.form['pickup_address']

        recipient_name = request.form['recipient_name']
        recipient_email = request.form['recipient_email']
        recipient_phone = request.form['recipient_phone']
        delivery_address = request.form['delivery_address']

        container_type = request.form['container_type']
        weight = request.form['weight']
        special_instructions = request.form.get('special_instructions', '')  # Optional field
        departure_port = request.form['departure_port']
        destination_port = request.form['destination_port']
        shipment_date = request.form['shipment_date']

        # Create a new booking
        new_booking = {
            "id": len(bookings) + 1,
            "user_id": user_id,
            "sender": {
                "name": sender_name,
                "email": sender_email,
                "phone": sender_phone,
                "pickup_address": pickup_address
            },
            "recipient": {
                "name": recipient_name,
                "email": recipient_email,
                "phone": recipient_phone,
                "delivery_address": delivery_address
            },
            "shipment_details": {
                "container_type": container_type,
                "weight": weight,
                "special_instructions": special_instructions,
                "departure_port": departure_port,
                "destination_port": destination_port,
                "shipment_date": shipment_date
            }
        }

        # Save the booking
        bookings.append(new_booking)
        save_data('bookings.json', bookings)

        # Redirect to dashboard
        return redirect(url_for('dashboard'))

    return render_template('book.html')


@app.route('/booking/<int:booking_id>')
def view_booking(booking_id):
    bookings = load_data('bookings.json')
    booking = next((b for b in bookings if b['id'] == booking_id), None)

    if not booking:
        return "Booking not found.", 404

    return render_template('booking_details.html', booking=booking)



@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Load user data
    users = load_data('users.json')
    user = next((u for u in users if u['id'] == user_id), None)

    # Load bookings for this user
    bookings = load_data('bookings.json')
    user_bookings = [b for b in bookings if b['user_id'] == user_id]

    return render_template('dashboard.html', user=user, bookings=user_bookings)


@app.route('/ports')
def ports():
    ports = load_data('ports.json')
    return jsonify(ports)


@app.route('/logout')
def logout():
	session.pop('user_id', None)
	return redirect(url_for('index'))



if __name__ == '__main__':
	if not os.path.exists("data"):
		os.makedirs("data")
	app.run(debug=True)

