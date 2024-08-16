import os
import logging

from flask import Flask, render_template, request, jsonify, redirect, url_for
from devices.SerialTestFixture import SerialTestFixture, get_ports
import serial

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize available ports and SerialTestFixture objects
port_dict = {}
num_ports = 0

app = Flask(__name__)

# Function to get form information for a specific tab
def update_serial_fixture(tabs):
    port = request.form.get(f'port{tabs}')
    baud_rate = int(request.form.get(f'baud_rate{tabs}'))
    parity_text = request.form.get(f'parity{tabs}')
    data_bits = int(request.form.get(f'data_bits{tabs}'))
    stop_bits = float(request.form.get(f'stop_bits{tabs}'))

    # Map the parity from text to serial module constant
    parity_map = {
        'Even': serial.PARITY_EVEN,
        'E' : serial.PARITY_EVEN,
        'Odd': serial.PARITY_ODD,
        'O' : serial.PARITY_ODD,
        'None': serial.PARITY_NONE,
        'N' : serial.PARITY_NONE
    }

    return port, baud_rate, parity_map.get(parity_text, serial.PARITY_NONE), data_bits, stop_bits

# Function to close the port and log the event
def close_port(port_info):
    port_info[0].close()
    logger.info("Closed")
    logger.info(f"Port Open: {port_info[0].is_port_open()}")

# Default route rendering the summary page
@app.route("/", methods=['GET', 'POST'])
def summary():
    return render_template(
        "summary.html",
        available_ports=get_ports(),
        num_ports=num_ports,
        port_dict=port_dict
    )

# Route to setup the ports based on the form data
@app.route("/setup", methods=['POST'])
def setup():
    global num_ports
    
    for tabs in port_dict:
        if port_dict[tabs][1] == 'OPEN':  # If the port is open, update its configurations
            try:
                port, baud_rate, parity, data_bits, stop_bits = update_serial_fixture(tabs)
                # Update the SerialTestFixture properties
                port_dict[tabs][0]._SerialTestFixture__port = port
                port_dict[tabs][0]._SerialTestFixture__baud_rate = baud_rate
                port_dict[tabs][0]._SerialTestFixture__parity = parity
                port_dict[tabs][0]._SerialTestFixture__data_bits = data_bits
                port_dict[tabs][0]._SerialTestFixture__stop_bits = stop_bits

                logger.info("Opened")
                port_dict[tabs][0].setup()
                logger.info(f"Port Open: {port_dict[tabs][0].is_port_open()}")
                
            except serial.serialutil.SerialException as e:
                logger.error('Port is already open')
                logger.error(f'Error: {e}')
        elif port_dict[tabs][1] == 'CLOSED':  # If the port is closed, close it
            close_port(port_dict[tabs])

    logger.info(port_dict)
    return redirect(url_for('summary'))

# Route to add a new device (port)
@app.route("/add-devices", methods=['POST'])
def add():
    global num_ports
    num_ports += 1

    # Adding a new SerialTestFixture object with initial state CLOSED and other default values
    port_dict[num_ports] = [SerialTestFixture(), 'CLOSED', None, False]
    logger.info(f"Added device: {port_dict[num_ports]}")
    
    return redirect(url_for('summary'))

# Route to delete the last added device (port)
@app.route("/delete-devices", methods=['POST'])
def delete():
    global num_ports
    
    if num_ports > 0:
        logger.info(f"Deleting device: {port_dict[num_ports]}")
        del port_dict[num_ports]
        num_ports -= 1
    
    return redirect(url_for('summary'))

# Route to update the state (OPEN/CLOSED) of a port
@app.route("/open-ports", methods=['POST'])
def update():
    button_id = int(request.json.get('button_id'))  
    new_state = request.json.get('new_state')

    if button_id in port_dict:
        port_dict[button_id][1] = new_state
        logger.info(f"Updated port {button_id} to new state: {new_state}")
        return jsonify(new_state=new_state), 200
    return jsonify(error="Invalid port index"), 400

# Route to send write data to the specified port
@app.route("/send-write", methods=['POST'])
def send_write():
    data = request.json
    port_index = int(data.get('port_index'))
    write_data = data.get('write')

    logger.info(f"Sending write data: {write_data} to port {port_index}")

    if port_dict.get(port_index) and port_dict[port_index][1] == 'OPEN':
        port_dict[port_index][0].write(write_data)  

    return jsonify(read_data='')

# Route to read data from the specified port
@app.route("/send-read", methods=['POST'])
def send_read():
    data = request.json
    port_index = int(data.get('port_index'))
    read_size = int(data.get('read'))
    
    logger.info(f"Received request to read {read_size} bytes from port {port_index}")

    try:
        if port_dict.get(port_index) and port_dict[port_index][1] == 'OPEN':
            read_bytes = port_dict[port_index][0].read(read_size)
            logger.info(f"Read {read_size} bytes: {read_bytes}")

            read_data = read_bytes.decode('utf-8', errors='ignore')
            logger.info(f"Read data from port {port_index}: {read_data}")

            # If logging is enabled, append the read data to the log file
            if port_dict[port_index][3] and read_bytes:
                log_file_path = port_dict[port_index][2]
                try:
                    with open(log_file_path, 'ab') as file:
                        file.write(read_bytes)
                        logger.info(f"Appended read data to log file: {log_file_path}")
                except IOError as e:
                    logger.error(f"Error writing to log file: {log_file_path} - {e}")
                    return jsonify(error=f"Error writing to log file: {e}"), 500

            return jsonify(read_data=read_data), 200
        return jsonify(error="Port is not open"), 400
    except KeyError:
        logger.error(f"Invalid port index {port_index}")
        return jsonify(error="Invalid port index"), 400
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify(error=str(e)), 500

# Route to create a log file for the specified port
@app.route("/create-log", methods=['POST'])
def create_log():
    try:
        data = request.json
        file_path = data.get('file_path')
        file_name = f"{data.get('file_name')}.bin"
        button_id = int(data.get('buttonId'))

        full_path = os.path.join(file_path, file_name)
        port_dict[button_id][2] = full_path

        # Create the log directory if it does not exist
        if file_path and not os.path.exists(file_path):
            os.makedirs(file_path)
            
        logger.info(f"Log file created at: {full_path}")
        return jsonify(success=True), 200
    except Exception as e:
        logger.error(f"Error creating log file: {e}")
        return jsonify(success=False, error=str(e)), 500

# Route to toggle logging state for the specified port
@app.route("/toggle-logging", methods=['POST'])
def toggle_logging():
    try:
        data = request.json
        logger.info(f"Data received: {data}")

        logging_state = data.get('newState')
        button_id = int(data.get('buttonId'))

        logger.info(f"Toggling logging for button ID: {button_id} to state: {logging_state}")

        if button_id in port_dict:
            port_dict[button_id][3] = logging_state == 'Logging: True'
            logger.info(f'Logging {"ON" if port_dict[button_id][3] else "OFF"} for port id {button_id}')
            return jsonify(success=True), 200
        return jsonify(success=False, error="Invalid button ID"), 400
    except Exception as e:
        logger.error(f"Error toggling logging state: {e}")
        return jsonify(success=False, error=str(e)), 500

# Route to get information about all ports
@app.route("/get-port-info", methods=['GET'])
def get_port_info():
    info = [{
        'port': port[0]._SerialTestFixture__port,
        'State': port[1],
        'File Path': port[2],
        'Logging': port[3]
    } for port in port_dict.values()]
    
    return jsonify({'ports': info}), 200

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)