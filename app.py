from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

import json
import logging
import os
import requests

# Configure logging
logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ensure session functionality


# Load the environment variables from the file
load_dotenv("API_keys.env")

# Access the variables
MAERSK_CLIENT_ID = os.getenv("MAERSK_CLIENT_ID")
MAERSK_CLIENT_SECRET = os.getenv("MAERSK_CLIENT_SECRET")

# Debug to check if variables are loaded correctly
print(f"Client ID: {MAERSK_CLIENT_ID}")
print(f"Client Secret: {MAERSK_CLIENT_SECRET}")



def get_access_token():
    url = "https://api.maersk.com/customer-identity/oauth/v2/access_token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": MAERSK_CLIENT_ID,
        "client_secret": MAERSK_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    print("Requesting access token with the following payload:")
    print(payload)

    response = requests.post(url, headers=headers, data=payload)

    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")

    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"Access token retrieved: {token}")
        return token
    else:
        raise Exception(f"Failed to get access token: {response.text}")




def get_container_status(container_id):
    token = get_access_token()
    url = f"https://api.maersk.com/containers/{container_id}/tracking"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch container status: {response.text}")


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
        container_id = request.form['container_id']
        app.logger.debug(f"Received container_id: {container_id}")
        try:
            tracking_result = get_container_status(container_id)
            app.logger.debug(f"Tracking result: {tracking_result}")
        except Exception as e:
            tracking_result = {"error": str(e)}
            app.logger.error(f"Error fetching tracking data: {e}")

    return render_template('track.html', tracking_result=tracking_result)

@app.route('/track_shipment/<int:shipment_id>')
def track_shipment(shipment_id):
    bookings = load_data('bookings.json')
    booking = next((b for b in bookings if b['id'] == shipment_id), None)

    if not booking:
        return "Shipment not found.", 404

    return render_template('track_shipment.html', booking=booking)



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


@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    bookings = load_data('bookings.json')
    updated_bookings = [b for b in bookings if b['id'] != booking_id or b['user_id'] != user_id]

    # Save the updated bookings back to the JSON file
    save_data('bookings.json', updated_bookings)

    return redirect(url_for('dashboard'))

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

    # Debugging: Print bookings
    print("User Bookings:", user_bookings)

    return render_template('dashboard.html', user=user, bookings=user_bookings)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Ensure the user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Load user data
    users = load_data('users.json')
    user = next((u for u in users if u['id'] == user_id), None)

    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Update user data
        user['name'] = name
        user['email'] = email
        user['password'] = password

        # Save updated user data
        save_data('users.json', users)

        return redirect(url_for('dashboard'))

    return render_template('profile.html', user=user)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/ports')
def ports():
    ports = load_data('ports.json')
    return jsonify(ports)


@app.route('/logout')
def logout():
	session.pop('user_id', None)
	return redirect(url_for('index'))


@app.route('/delete_account', methods=['POST'])
def delete_account():
    # Ensure the user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Load user data
    users = load_data('users.json')
    bookings = load_data('bookings.json')

    # Remove the user
    updated_users = [u for u in users if u['id'] != user_id]
    save_data('users.json', updated_users)

    # Remove the user's bookings
    updated_bookings = [b for b in bookings if b['user_id'] != user_id]
    save_data('bookings.json', updated_bookings)

    # Log the user out
    session.pop('user_id', None)

    # Optionally, log account deletion
    logging.warning(f"User {user_id} and all associated data have been deleted.")

    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Load users data
        users = load_data('users.json')
        user = next((u for u in users if u['email'] == email), None)

        if user:
            # Redirect to reset password page with user's ID
            return redirect(url_for('reset_password', user_id=user['id']))
        else:
            return "Error: Email not found.", 404

    return render_template('forgot_password.html')


@app.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    # Load user data
    users = load_data('users.json')
    user = next((u for u in users if u['id'] == user_id), None)

    if not user:
        return "Error: User not found.", 404

    if request.method == 'POST':
        new_password = request.form['password']

        # Update the user's password
        user['password'] = new_password
        save_data('users.json', users)

        return redirect(url_for('login'))

    return render_template('reset_password.html', user=user)



if __name__ == '__main__':
	if not os.path.exists("data"):
		os.makedirs("data")
	app.run(debug=True)