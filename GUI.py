#GUI imports
from guizero import App, Text, TextBox, PushButton, Picture, ButtonGroup, Box, Window, info
#Time and other imports
import random
import os
from datetime import datetime, timedelta
import time
#I2C imports
import smbus

#Appends pressed button numbers to the textbox field
def input_to_textbox(user_input):
    text_box.append(user_input)

#Function to clear the textbox
def clear_textbox():
    text_box.clear()

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

def open_door(data):
    bus.write_byte(DEVICE_ADDR, data)

def condition():
    # Extract error states and IR sensor states for both boxes
    received_byte = bus.read_byte(DEVICE_ADDR)
    box1_error_state = received_byte // 1000
    box1_ir_sensor_state = (received_byte % 1000) // 100
    box2_error_state = (received_byte % 100) // 10
    box2_ir_sensor_state = received_byte % 10
   
    return (box1_error_state, box1_ir_sensor_state), (box2_error_state, box2_ir_sensor_state)

#Sends the data in the textbox

def send_data():
    entered_code = text_box.value.strip()
    used_codes = load_used_codes()
    check_code(entered_code)
    if entered_code == "":
        print("Entered code is empty.")
        app.error("VIGA", "     Tühi kood!     ")
    elif entered_code in used_codes:
        if code_expired(entered_code):
            print("Code has expired:", entered_code)
            app.error("VIGA", "     Kood on aegunud!     ")
            remove_code_from_file(entered_code)
        else:
            print("Processing code:", entered_code)
            door_number = used_codes[entered_code]
            print("door nmber:", door_number)
            open_door(door_number)
            time.sleep(1)
            box1_data, box2_data = condition()
            # Process the retrieved data for the specified door
            if door_number == 1:
                door, ir_sensor_state = box1_data
            else:
                door, ir_sensor_state = box2_data
            if door == 1:
                app.info("INFO", "     Uks ei lainud lahti, ime munni ja hakka nutma pede!     ")
                return  # Exit function if door didn't open
            timestamp = generate_timestamp()
            code_timestamps[entered_code] = timestamp
            app.info("INFO", "     Kapp avatud!     ")
            time.sleep(8)
            if door == 2:
                app.info("INFO", "     Uks ei lainud kinni tagasi!     ")
            elif door == 0:
                app.info("INFO", "     Kõik ok!     ")
    elif entered_code == "1337":
        print("Processing code:", entered_code)
    else:
        print("Wrong code:", entered_code)
        app.error("VIGA", "     Vale kood!     ")
       
    text_box.clear()


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

#Function to change the screen when admin code is entered
def check_code(code):
    #Function that opens the selected box
    def open_box():
        radioBoxValue = int(radioBoxes.value)
        adminWindow.info("AVA KAPP", "Avasid kapi {}".format(radioBoxValue))
    def open_door_admin():
        data = int(radioBoxes.value)
        bus.write_byte(DEVICE_ADDR, data)
       
    #Generate a random 6-digit code
    def generate_code():
        random_code = str(random.randint(100000, 999999))
       
        #Check if the code has been used before generating a new one
        while random_code in used_codes:
            random_code = str(random.randint(100000, 999999))
        radioBoxValue = int(radioBoxes.value)
        save_used_codes(random_code,radioBoxValue)
       

        adminWindow.info("INFO", "Genereeritud kapile {} kood {}".format(radioBoxValue, random_code))
       
    if code == '1337':
        adminWindow = Window(app, title = "ADMINI KAPP", width= 400, height = 300)
        window_box = Box(adminWindow, layout = "grid")
        radioBoxes = ButtonGroup(window_box, options=[["KAPP 1", 1], ["KAPP 2", 2]], grid=[0,1], align = "left")
        buttonOpenBox = PushButton(window_box, text="AVA KAPP", grid=[0,0], align = "top", width=15, command=open_door_admin)
        generate_button = PushButton(window_box, text="Generate Code", grid=[0, 2], align="top", width=15, command=generate_code)
    if code == '0000':
        exit()



app = App(title = "NUTIKAPP", width= 1920, height = 1080)
#Used for creating empty space at the top of the screen
center_pad = Box(app, align="top", height=150, width="fill")
#Used for putting all the buttons, picture etc. to a container
center_box = Box(app, layout = "grid")

welcome_message = Text(center_box, text = "SISESTA KOOD", font = "Times New Roman", grid = [1,0], size=30)

text_box = TextBox(center_box, grid = [1,1], width=6)
text_box.text_size = 30
text_box.text_color = "#f3941c"
text_box.bg = "#e0dcdc"

used_codes = set()

code_timestamps = {}

#Initialize the I2C bus
DEVICE_BUS = 1

#Device I2C address
#(will be left shifted to add the read write bit)
DEVICE_ADDR =10
bus = smbus.SMBus(DEVICE_BUS)
data = 1

button_width = 5
button_height = 2

#When a button is pressed the function in 'command' is executed and arguments given is in 'args'
button1 = PushButton(center_box, text="1", grid=[0,2], align = "right", width=button_width,height=button_height, command=input_to_textbox, args=['1'])
button2 = PushButton(center_box, text="2", grid=[1,2], width=button_width,height=button_height,  command=input_to_textbox, args=['2'])
button3 = PushButton(center_box, text="3", grid=[2,2], width=button_width,height=button_height,  command=input_to_textbox, args=['3'])
button4 = PushButton(center_box, text="4", grid=[0,3], align = "right", width=button_width,height=button_height,  command=input_to_textbox, args=['4'])
button5 = PushButton(center_box, text="5", grid=[1,3], width=button_width, height=button_height, command=input_to_textbox, args=['5'])
button6 = PushButton(center_box, text="6", grid=[2,3], width=button_width,height=button_height,  command=input_to_textbox, args=['6'])
button7 = PushButton(center_box, text="7", grid=[0,4], align = "right", width=button_width, height=button_height, command=input_to_textbox, args=['7'])
button8 = PushButton(center_box, text="8", grid=[1,4], width=button_width,height=button_height,  command=input_to_textbox, args=['8'])
button9 = PushButton(center_box, text="9", grid=[2,4], width=button_width,height=button_height,  command=input_to_textbox, args=['9'])
buttonD = PushButton(center_box, text="DEL", grid=[0,5], align = "right", width=button_width,height=button_height,  command=clear_textbox)
button0 = PushButton(center_box, text="0", grid=[1,5], width=button_width,height=button_height, command=input_to_textbox, args=['0'])
buttonE = PushButton(center_box, text="ENT", grid=[2,5], width=button_width,height=button_height, command=send_data)

button1.text_size=20
button2.text_size=20
button3.text_size=20
button4.text_size=20
button5.text_size=20
button6.text_size=20
button7.text_size=20
button8.text_size=20
button9.text_size=20
buttonD.text_size=20
button0.text_size=20
buttonE.text_size=20

picture = Picture(center_box, image = "logo.gif", grid = [1,6])

app.full_screen = True
app.display()
