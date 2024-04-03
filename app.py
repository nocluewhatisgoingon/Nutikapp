from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
import smbus
import time
import random

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


#Removes the code once it has been used
def remove_code_from_file(code):
    filename = "codes.txt"
    temp_filename = "temp_codes.txt"  # Temporary file to store modified contents

    with open(filename, "r") as input_file, open(temp_filename, "w") as output_file:
        for line in input_file:
            if not line.startswith(code + ":"):  # Skip the line with the code to be removed
                output_file.write(line)

    # Rename temporary file to original filename to replace it
    os.replace(temp_filename, filename)



def open_door(a):
    bus.write_byte(DEVICE_ADDR, a)
   
# Call the condition() function to get error state and IR sensor state



def condition():
    # Extract error states and IR sensor states for both boxes
    received_byte = bus.read_byte(DEVICE_ADDR)
    box1_error_state = received_byte // 1000
    box1_ir_sensor_state = (received_byte % 1000) // 100
    box2_error_state = (received_byte % 100) // 10
    box2_ir_sensor_state = received_byte % 10
   
    return (box1_error_state, box1_ir_sensor_state), (box2_error_state, box2_ir_sensor_state)



@app.route('/process_data', methods=['POST'])
def process_data():
    entered_code = request.form['code']
    used_codes = load_used_codes()
   
    if entered_code == "":
        return jsonify({'message': 'No code was entered'})
   
    if entered_code == "0000":
        return jsonify({'message': 'Admin panel deactivated', 'hide_admin_panel': True})

    if entered_code in used_codes:
        if code_expired(entered_code):
            remove_code_from_file(entered_code)
            return jsonify({'message': 'Code has expired'})
        else:
            door_number = used_codes[entered_code]
            open_door(door_number)  # Open the door linked with the entered code
            time.sleep(1)
           
            # Retrieve error state and IR sensor state for the specified door
            box1_data, box2_data = condition()
           
            # Process the retrieved data for the specified door
            if door_number == 1:
                error_state, ir_sensor_state = box1_data
            else:
                error_state, ir_sensor_state = box2_data
           
            if error_state == 1:
                return jsonify({'message': f'Door {door_number} did not open'})
            timestamp = generate_timestamp()
            code_timestamps[entered_code] = timestamp
            time.sleep(8)
            if error_state == 2:                
                return jsonify({'message': f'Door {door_number} did not close again'})
            elif error_state == 0:
                return jsonify({'message': f'Everything is OK for Door {door_number}'})
    elif entered_code == "1337":
        return jsonify({'message': 'Admin panel activated', 'show_admin_panel': True})
    else:
        return jsonify({'message': 'Wrong code'})




@app.route('/generate_new_code', methods=['POST'])
def generate_new_code():
    global used_codes
    if used_codes is None:
        used_codes = load_used_codes()

    selected_door_str = request.form.get('selected_door')  
    if selected_door_str is None:
        return jsonify({'message': 'No door selected'})

    try:
        selected_door = int(selected_door_str)  
    except ValueError:
        return jsonify({'message': 'Invalid door number'})

    random_code = str(random.randint(100000, 999999))  

    while random_code in used_codes:
        random_code = str(random.randint(100000, 999999))
       
    save_used_codes(random_code, selected_door)  # Save the code and its linked door
    return jsonify({'message': 'New code generated', 'code': random_code, 'door': selected_door})


     


@app.route('/open_door', methods=['POST'])
def open_door_route():
    door_number = int(request.form['door_number'])
    open_door(door_number)
    time.sleep(1)  # Add a delay to allow the door to open and close
   
    # Retrieve error state and IR sensor state for the specified door
    box1_data, box2_data = condition()
   
    # Process the retrieved data for the specified door
    if door_number == 1:
        error_state, _ = box1_data
    else:
        error_state, _ = box2_data
   
    if error_state == 1:
        return jsonify({'message': 'Door ' + str(door_number) + ' did not open'})
   
    time.sleep(10)
    # Retrieve error state again after waiting for the door to close
    box1_data, box2_data = condition()
   
    # Process the retrieved data for the specified door again
    if door_number == 1:
        error_state, _ = box1_data
    else:
        error_state, _ = box2_data
   
    if error_state == 2:
        return jsonify({'message': 'Door ' + str(door_number) + ' did not close again'})
    elif error_state == 0:
        return jsonify({'message': 'Door ' + str(door_number) + ' opened and closed successfully'})


# Define a route to provide sensor data
@app.route('/get_sensor_data')
def get_sensor_data():
    # Call the condition() function to get sensor data
    box1_data, box2_data = condition()
    box1_ir_sensor_state = box1_data[1]
    box2_ir_sensor_state = box2_data[1]
   
    # Return sensor data as JSON
    return jsonify({'ir_sensor_state_1': box1_ir_sensor_state, 'ir_sensor_state_2': box2_ir_sensor_state})

# Other routes and functions remain unchanged  
     
       

# Load used codes from a file
def load_used_codes():
    used_codes = {}
    filename = "codes.txt"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                code, door = line.strip().split(":")
                used_codes[code] = int(door)
    return used_codes

# Save used codes to a file
def save_used_codes(code, door):
    filename = "codes.txt"
    with open(filename, "a") as file:
        file.write(f"{code}:{door}\n")

#Generate a timestamp for a code
def generate_timestamp():
    return datetime.now()

#Check if a code has expired
def code_expired(code):
    if code in code_timestamps:
        expiration_time = code_timestamps[code] + timedelta(minutes=1)
        return datetime.now() > expiration_time
    return False

@app.route('/view_codes')
def view_codes():
    try:
        with open('codes.txt', 'r') as file:
            codes = file.read()
        return codes
    except FileNotFoundError:
        return 'Error: codes.txt not found', 404



   
used_codes = set()

code_timestamps = {}

#Initialize the I2C bus
DEVICE_BUS = 1

#Device I2C address
#(will be left shifted to add the read write bit)
DEVICE_ADDR =10
bus = smbus.SMBus(DEVICE_BUS)
data = 1

if __name__ == '__main__':
    app.run(host='172.20.10.3', port=5000, debug=True)
