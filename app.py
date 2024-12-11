from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta

import json
import logging
import os
import requests
import string
import random

# Configure logging
logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ensure session functionality


# # Load the environment variables from the file
# load_dotenv("API_keys.env")
#
# # Access the variables
# MAERSK_CLIENT_ID = os.getenv("MAERSK_CLIENT_ID")
# MAERSK_CLIENT_SECRET = os.getenv("MAERSK_CLIENT_SECRET")
#
# # Debug to check if variables are loaded correctly
# print(f"Client ID: {MAERSK_CLIENT_ID}")
# print(f"Client Secret: {MAERSK_CLIENT_SECRET}")



# def get_access_token():
#     url = "https://api.maersk.com/customer-identity/oauth/v2/access_token"
#     payload = {
#         "grant_type": "client_credentials",
#         "client_id": MAERSK_CLIENT_ID,
#         "client_secret": MAERSK_CLIENT_SECRET,
#     }
#     headers = {"Content-Type": "application/x-www-form-urlencoded"}
#
#     print("Requesting access token with the following payload:")
#     print(payload)
#
#     response = requests.post(url, headers=headers, data=payload)
#
#     print(f"Response status code: {response.status_code}")
#     print(f"Response body: {response.text}")
#
#     if response.status_code == 200:
#         token = response.json().get("access_token")
#         print(f"Access token retrieved: {token}")
#         return token
#     else:
#         raise Exception(f"Failed to get access token: {response.text}")
#
#
# #
# #
# def get_container_status(container_id):
#     token = get_access_token()
#     url = f"https://api.maersk.com/containers/{container_id}/tracking"
#     headers = {"Authorization": f"Bearer {token}"}
#
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         raise Exception(f"Failed to fetch container status: {response.text}")

#
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

########################################


# Average container ship speed in km/h
SHIP_SPEED_KMH = 46

# Example port distances (can expand this dictionary)
PORT_DISTANCES = {
    ("Port of Rotterdam", "Port of Shanghai"): 20500,
    ("Port of Rotterdam", "Port of Antwerp"): 120,
    ("Port of Rotterdam", "Port of Singapore"): 15900,
    ("Port of Rotterdam", "Port of Hamburg"): 620,
    ("Port of Rotterdam", "Port of Dubai"): 11800,
    ("Port of Rotterdam", "Port of New York"): 6200,
    ("Port of Rotterdam", "Port of Los Angeles"): 17000,
    ("Port of Rotterdam", "Port of Hong Kong"): 19600,
    ("Port of Rotterdam", "Port of Busan"): 20900,
    ("Port of Rotterdam", "Port of Tokyo"): 21500,
    ("Port of Rotterdam", "Port of Sydney"): 22600,
    ("Port of Rotterdam", "Port of Santos"): 9700,
    ("Port of Rotterdam", "Port of Durban"): 9700,

    ("Port of Shanghai", "Port of Singapore"): 3800,
    ("Port of Shanghai", "Port of Hamburg"): 20800,
    ("Port of Shanghai", "Port of Dubai"): 12000,
    ("Port of Shanghai", "Port of New York"): 18000,
    ("Port of Shanghai", "Port of Los Angeles"): 9600,
    ("Port of Shanghai", "Port of Hong Kong"): 1300,
    ("Port of Shanghai", "Port of Busan"): 900,
    ("Port of Shanghai", "Port of Tokyo"): 1800,
    ("Port of Shanghai", "Port of Sydney"): 8400,
    ("Port of Shanghai", "Port of Santos"): 19400,
    ("Port of Shanghai", "Port of Durban"): 16000,

    ("Port of Antwerp", "Port of Singapore"): 15900,
    ("Port of Antwerp", "Port of Hamburg"): 620,
    ("Port of Antwerp", "Port of Dubai"): 11800,
    ("Port of Antwerp", "Port of New York"): 6200,
    ("Port of Antwerp", "Port of Los Angeles"): 17000,
    ("Port of Antwerp", "Port of Hong Kong"): 19600,
    ("Port of Antwerp", "Port of Busan"): 20900,
    ("Port of Antwerp", "Port of Tokyo"): 21500,
    ("Port of Antwerp", "Port of Sydney"): 22600,
    ("Port of Antwerp", "Port of Santos"): 9700,
    ("Port of Antwerp", "Port of Durban"): 9700,

    ("Port of Singapore", "Port of Dubai"): 5500,
    ("Port of Singapore", "Port of New York"): 15700,
    ("Port of Singapore", "Port of Los Angeles"): 14400,
    ("Port of Singapore", "Port of Hong Kong"): 2600,
    ("Port of Singapore", "Port of Busan"): 4700,
    ("Port of Singapore", "Port of Tokyo"): 6000,
    ("Port of Singapore", "Port of Sydney"): 6300,
    ("Port of Singapore", "Port of Santos"): 19800,
    ("Port of Singapore", "Port of Durban"): 7200,

    ("Port of Dubai", "Port of New York"): 11300,
    ("Port of Dubai", "Port of Los Angeles"): 14500,
    ("Port of Dubai", "Port of Hong Kong"): 6300,
    ("Port of Dubai", "Port of Busan"): 7600,
    ("Port of Dubai", "Port of Tokyo"): 8200,
    ("Port of Dubai", "Port of Sydney"): 12000,
    ("Port of Dubai", "Port of Santos"): 19400,
    ("Port of Dubai", "Port of Durban"): 6600,

    ("Port of New York", "Port of Los Angeles"): 4000,
    ("Port of New York", "Port of Hong Kong"): 20900,
    ("Port of New York", "Port of Busan"): 20700,
    ("Port of New York", "Port of Tokyo"): 20200,
    ("Port of New York", "Port of Sydney"): 23200,
    ("Port of New York", "Port of Santos"): 7900,
    ("Port of New York", "Port of Durban"): 12200,

    ("Port of Los Angeles", "Port of Hong Kong"): 11600,
    ("Port of Los Angeles", "Port of Busan"): 9700,
    ("Port of Los Angeles", "Port of Tokyo"): 8800,
    ("Port of Los Angeles", "Port of Sydney"): 12000,
    ("Port of Los Angeles", "Port of Santos"): 10100,
    ("Port of Los Angeles", "Port of Durban"): 17400,

    ("Port of Hong Kong", "Port of Busan"): 2900,
    ("Port of Hong Kong", "Port of Tokyo"): 2900,
    ("Port of Hong Kong", "Port of Sydney"): 7400,
    ("Port of Hong Kong", "Port of Santos"): 18900,
    ("Port of Hong Kong", "Port of Durban"): 11500,

    ("Port of Busan", "Port of Tokyo"): 1400,
    ("Port of Busan", "Port of Sydney"): 7700,
    ("Port of Busan", "Port of Santos"): 18900,
    ("Port of Busan", "Port of Durban"): 16100,

    ("Port of Tokyo", "Port of Sydney"): 7800,
    ("Port of Tokyo", "Port of Santos"): 19000,
    ("Port of Tokyo", "Port of Durban"): 16100,

    ("Port of Sydney", "Port of Santos"): 19000,
    ("Port of Sydney", "Port of Durban"): 11000
}

def calculate_eta(departure_port, destination_port, shipment_date):
    """
    Calculates ETA based on port distances and shipping speed.
    """
    # Get distance or handle missing case
    distance = PORT_DISTANCES.get((departure_port, destination_port)) or PORT_DISTANCES.get((destination_port, departure_port))
    if not distance:
        return "ETA not available (distance not found)"

    # Calculate travel time in hours
    travel_time_hours = distance / SHIP_SPEED_KMH

    # Convert to days and round up
    travel_time_days = int(travel_time_hours // 24 + (1 if travel_time_hours % 24 > 0 else 0))

    # Add travel time to shipment date
    shipment_date = datetime.strptime(shipment_date, '%Y-%m-%d')
    eta_date = shipment_date + timedelta(days=travel_time_days)
    return eta_date.strftime('%Y-%m-%d')  # Return as a formatted date



def calculate_shipment_status(shipment_date, eta):
    """
    Determines the shipment status based on the current date, shipment date, and ETA.
    """
    today = datetime.today().date()
    shipment_date = datetime.strptime(shipment_date, '%Y-%m-%d').date()
    eta_date = datetime.strptime(eta, '%Y-%m-%d').date()

    if today < shipment_date:
        return "Preparing"  # Before shipment starts
    elif shipment_date <= today < eta_date:
        return "In Transit"  # Shipment is on the way
    elif today == eta_date:
        return "Arriving Today"  # Shipment arrives today
    else:
        return "Delivered"  # Shipment has been delivered



# @app.route('/track', methods=['GET', 'POST'])
# def track():
#     tracking_result = None
#     if request.method == 'POST':
#         container_id = request.form['container_id']
#         app.logger.debug(f"Received container_id: {container_id}")
#         try:
#             # Fetch tracking info (use mock data or integrate API later)
#             tracking_result = get_container_status(container_id)
#             app.logger.debug(f"Tracking result: {tracking_result}")
#         except Exception as e:
#             tracking_result = {"error": str(e)}
#             app.logger.error(f"Error fetching tracking data: {e}")
#
#     return render_template('track.html', tracking_result=tracking_result)

@app.route('/track', methods=['GET', 'POST'])
def track():
    tracking_result = None
    if request.method == 'POST':
        container_id = request.form['container_id']

        # Look for container information in bookings.json
        bookings = load_data('bookings.json')

        # Validate bookings and find the container
        tracking_result = next((b for b in bookings if b.get('container_id') == container_id), None)

        if tracking_result:
            # Calculate ETA and status
            eta = calculate_eta(
                tracking_result['shipment_details']['departure_port'],
                tracking_result['shipment_details']['destination_port'],
                tracking_result['shipment_details']['shipment_date']
            )
            tracking_result['eta'] = eta
            tracking_result['status'] = calculate_shipment_status(
                tracking_result['shipment_details']['shipment_date'], eta
            )
        else:
            # Handle case where container ID is not found
            tracking_result = {"error": "Container ID not found. Please check the ID and try again."}

    return render_template('track.html', tracking_result=tracking_result)




# @app.route('/track_shipment/<int:shipment_id>')
# def track_shipment(shipment_id):
#     bookings = load_data('bookings.json')
#     booking = next((b for b in bookings if b['id'] == shipment_id), None)
#
#     if not booking:
#         return "Shipment not found.", 404
#
#     # Calculate ETA
#     eta = calculate_eta(
#         booking["shipment_details"]["departure_port"],
#         booking["shipment_details"]["destination_port"],
#         booking["shipment_details"]["shipment_date"]
#     )
#     booking["eta"] = eta
#
#     return render_template('track_shipment.html', booking=booking)

@app.route('/track_shipment/<int:shipment_id>')
def track_shipment(shipment_id):
    bookings = load_data('bookings.json')
    booking = next((b for b in bookings if b['id'] == shipment_id), None)

    if not booking:
        return "Shipment not found.", 404

    # Calculate ETA and status
    eta = calculate_eta(
        booking["shipment_details"]["departure_port"],
        booking["shipment_details"]["destination_port"],
        booking["shipment_details"]["shipment_date"]
    )
    booking["eta"] = eta
    booking["status"] = calculate_shipment_status(
        booking["shipment_details"]["shipment_date"], eta
    )

    return render_template('track_shipment.html', booking=booking)


########################################

def generate_container_id():
    """
    Generates a random container ID.
    Format: 4 letters + 6 digits (e.g., "MSKU123456").
    """
    owner_code = ''.join(random.choices(string.ascii_uppercase, k=4))  # 4 random uppercase letters
    serial_number = ''.join(random.choices(string.digits, k=6))       # 6 random digits
    return f"{owner_code}{serial_number}"



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

        # Generate a random container ID
        container_id = generate_container_id()

        # Create a new booking
        new_booking = {
            "id": len(bookings) + 1,
            "container_id": container_id,  # Attach container ID
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