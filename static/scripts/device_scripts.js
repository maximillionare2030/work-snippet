$(document).ready(function() {

    // Handle button click to toggle port state OPEN/CLOSED
    $('.portButton').click(function() {
        var buttonId = $(this).attr('id').replace('button', '');
        var currentState = $(this).text();
        var newState = currentState === 'OPEN' ? 'CLOSED' : 'OPEN';

        // Send the new state to the server using AJAX
        $.ajax({
            url: '/open-ports',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ button_id: buttonId, new_state: newState }),
            success: function(response) {
                // Update the button text
                $('#button' + buttonId).text(response.new_state);
            }
        });
    });

    // Attach change events to each form control to handle AJAX updates
    $('#setup-form').on('change', 'select, .write-input, .read-input', function() {
        var portIndex = $(this).data('port-index');
        var inputData = {
            port: $(`select[name="port${portIndex}"]`).val(),
            baud_rate: $(`select[name="baud_rate${portIndex}"]`).val(),
            parity: $(`select[name="parity${portIndex}"]`).val(),
            data_bits: $(`select[name="data_bits${portIndex}"]`).val(),
            stop_bits: $(`select[name="stop_bits${portIndex}"]`).val()
        };

        $.ajax({
            url: '/setup',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ port_index: portIndex, input_data: inputData }),
            success: function(response) {
                console.log('Port settings updated successfully.');
            }
        });
    });

    // Handle the send-write button click event
    $('.send-write-button').click(function(event) {
        event.preventDefault(); // Prevent default form submission
        var portIndex = $(this).data('port-index');
        var writeData = $(`#writeInput${portIndex}`).val();

        $.ajax({
            url: '/send-write',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ port_index: portIndex, write: writeData }),
            success: function(response) {
                // Handle response if needed
                alert('Writing ' + writeData);
                console.log(response);
            }
        });
    });

    let readAllIntervals = {};

    // Handle the send-read button click event
    $('.send-read-button').click(function(event) {
        event.preventDefault(); // Prevent default form submission
        var portIndex = $(this).data('port-index');
        var readSize = $(`#readInput${portIndex}`).val();

        // Validate readSize
        if (!readSize || isNaN(readSize) || readSize <= 0) {
            alert("Please enter a valid read size.");
            return;
        }

        $.ajax({
            url: '/send-read',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ port_index: portIndex, read: readSize }),
            success: function(response) {
                if (response.read_data !== '') {
                    $(`#read_data${portIndex}`).attr("placeholder", function(index, currentValue) {
                        return currentValue + response.read_data + ' ';
                    });
                } else {
                    alert("Buffer Empty");

                    // Stop the interval if buffer is empty
                    clearInterval(readAllIntervals[portIndex]);
                    readAllIntervals[portIndex] = null;
                    $(`#read-all${portIndex}`).text('READ ALL');
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error(`Error: ${textStatus}, ${errorThrown}`);
                alert(`An error occurred: ${textStatus}`);
            }
        });
    });

    // Function to toggle reading all data periodically
    window.toggleReadAll = function(tabs) {
        const sendReadButton = document.getElementById(`send-read${tabs}`);
        const toggleButton = document.getElementById(`read-all${tabs}`);

        if (readAllIntervals[tabs]) {
            // If an interval exists, clear it to stop the process
            clearInterval(readAllIntervals[tabs]);
            readAllIntervals[tabs] = null;
            toggleButton.innerText = 'READ ALL';
        } else {
            // Set an interval to click the send-read button continually
            readAllIntervals[tabs] = setInterval(() => {
                $(sendReadButton).trigger('click');
            }, 1000);
            toggleButton.innerText = 'STOP READ ALL';
        }
    };

    // Function to toggle the visibility of the log popup
    function togglePopup(popupId) {
        var popup = document.getElementById(popupId);
        if (popup.style.display === "none" || popup.style.display === "") {
            popup.style.display = "block";
        } else {
            popup.style.display = "none";
        }
    }

    // Add event listeners for log buttons and popups
    const logButtons = document.querySelectorAll('.create-log-button');
    logButtons.forEach(button => {
        const tabs = button.getAttribute('id').replace('createLogButton', '');
        button.addEventListener('click', function() {
            togglePopup('logPopup' + tabs);
        });
    });

    // Add event listeners for all closePopupButtons
    const closeButtons = document.querySelectorAll('.closePopupButton');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const parentPopup = button.closest('.log-popup');
            parentPopup.style.display = "none";
        });
    });

});

// Logging Feature functions
function create_log(button) {
    // Get the port index from the clicked button's data attribute
    var tabs = button.getAttribute('data-port-index');

    // Get the values from the input fields
    var filePath = document.getElementById('file-path' + tabs).value;
    var fileName = document.getElementById('file-name' + tabs).value;

    // Send the data to the Flask route using fetch API
    fetch('/create-log', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            buttonId: tabs,
            file_path: filePath,
            file_name: fileName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Log file created successfully');
            // Hide the popup after successful creation
            var parentPopup = button.closest('.log-popup');
            parentPopup.style.display = "none";
        } else {
            alert('Failed to create log file.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function toggle_logging(button) {
    var button_id = button.getAttribute('data-port-index');
    var currentState = button.innerText;
    var newState = currentState === 'Logging: True' ? 'Logging: False' : 'Logging: True';

    fetch('/toggle-logging', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ newState: newState, buttonId: button_id })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            button.innerText = newState;
        } else {
            alert('Failed to toggle logging.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while processing your request: ' + error);
    });
}