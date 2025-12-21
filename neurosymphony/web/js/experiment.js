// Define variables and functions as properties of the window object
window.sliderData = [];
window.startTime;
window.intervalId;
window.currentTrack = 0;
window.currentTrack = JSON.parse(document.getElementById('tracks_index').textContent); // load track index to restore session

// Attach tracks to the window object for global access
window.tracks = JSON.parse(document.getElementById('tracksData').textContent); // Load tracks from a hidden element

window.buttonStates = []; // Store button states globally

window.switch_off = function (button) {
    button.value = "0";
    button.innerText = "Off";
    button.style.backgroundColor = "#a8aaac";
    button.style.color = "black";
}

window.switch_on = function (button) {
    button.innerText = "On";
    button.value = "1";
    button.style.backgroundColor = "#0066cc";
    button.style.color = "white";
}

window.toggleButtonState =function (button, index) {
    // Initialize button states array if it's empty
    if (!window.buttonStates[index]) {
        window.buttonStates[index] = false;
    }

    // Toggle the state
    window.buttonStates[index] = !window.buttonStates[index];

    // Update the button text and style based on the state
    if (window.buttonStates[index]) {
        window.switch_on(button);
    } else {
        window.switch_off(button);
    }
}



function closeRetryModal() {
    document.getElementById('retryModal').style.display = 'none';
}

function showRetryModal(retryFunction) {
    document.getElementById('retryModal').style.display = 'block';

    // Attach the retry function to the retry button's click event
    document.getElementById('retryButton').onclick = function() {
        closeRetryModal();
        retryFunction(); // Call the passed function when the user clicks "Retry"
    };
}

function retrySavingData() {
    window.saveData(function(success) {
        if (success) {
            closeRetryModal();
            clearQuestionnaireForm(); // Clear the form before showing the overlay
            document.getElementById('questionnaireOverlay').style.display = 'flex';
            document.getElementById('questionnaireOverlay').scrollTo({top: 0});
            window.questionnaireDurationStartTime = Date.now(); // Restart the timer for questionnaire duration
        } else {
            showRetryModal(); // Show the modal again if it fails again
        }
    });
}


// Define functions as global by attaching them to window
window.loadTrack = function (trackIndex) {
    if (trackIndex < window.tracks.length) {
        let waiting_text = document.getElementById('wait_loading_button_text').innerText;
        let play_button_text = document.getElementById('play_button_text').innerText;
        let progress_track_text = document.getElementById('track_text').innerText;

        let track = window.tracks[trackIndex];
        document.getElementById('trackTitle').innerText = `${progress_track_text} ${trackIndex + 1}`;
        document.getElementById('trackDescription').innerText = track.description;
        window.readingDurationStartTime = Date.now(); // Start the timer for reading duration
        let audioPlayer = document.getElementById('audioPlayer');
        audioPlayer.src = encodeURI(track.file); // Ensure URI encoding
        audioPlayer.preload = 'auto';

        let startButton = document.getElementById('startsong');
        startButton.disabled = true;
        startButton.innerText = waiting_text;

        // Reset sliders to 0 and disable them
        let toggleButtons = document.querySelectorAll('.toggle-button');
        toggleButtons.forEach(toggleButton => {
            window.switch_off(toggleButton);
            toggleButton.disabled = true;
        });

        audioPlayer.onerror = function () {
            console.error("Failed to load audio: ", track.file);
            alert("Impossibile caricare l'audio, controlla la connessione e ricarica la pagina!");
        };

        audioPlayer.oncanplaythrough = function () {
            // Enable the start button when the audio is ready to play
            startButton.disabled = false;
            startButton.innerText = play_button_text;
        };

        // Update track counter
        document.getElementById('trackCounter').innerText = `${progress_track_text} No. ${trackIndex + 1} di ${window.tracks.length}`;
        // document.getElementById('trackCounter').innerText = `${progress_track_text} ${trackIndex + 1}/${window.tracks.length}`;

        // Show description overlay
        window.readingDuration = Date.now() - window.readingDurationStartTime; // Capture reading duration
        window.startingDurationStartTime = Date.now(); // Start the timer for starting duration
        document.getElementById('descriptionOverlay').style.display = 'flex';

        window.sliderData = []; // Reset slider data for the new track
    } else {
        let submitbutton = document.getElementById('finish_experiment');
        submitbutton.click();
    }
};

window.close_description = function() {
    document.getElementById('descriptionOverlay').style.display = 'none';
    window.readingDuration = Date.now() - window.readingDurationStartTime; // Capture reading duration
    window.startingDurationStartTime = Date.now(); // Start the timer for starting duration
    }

window.startExperiment = function () {
    let startButton = document.getElementById('startsong');
    window.startingDuration = Date.now() - window.startingDurationStartTime; // Capture reading duration
    window.listeningDurationStartTime = Date.now(); // Start the timer for listening duration
    startButton.style.visibility = "hidden";
    window.startTime = Date.now();
    let audio = document.getElementById('audioPlayer');
    audio.play().catch(error => {
        console.error("Error playing audio:", error);
    });

    // Enable sliders when the song starts
    let toggleButtons = document.querySelectorAll('.toggle-button');
    toggleButtons.forEach(toggleButton => {
        toggleButton.disabled = false;
    });

    // Hide description overlay
    document.getElementById('descriptionOverlay').style.display = 'none';

    // Store the initial "101" value at the start
    let initialValues = Array.from(toggleButtons).map(toggleButton => 101);
    initialValues.unshift(0); // Timestamp 0
    window.sliderData.push(initialValues);

    window.intervalId = setInterval(() => {
        let timestamp = Date.now() - window.startTime;
        let values = Array.from(toggleButtons).map(toggleButton => toggleButton.value);
        values.unshift(timestamp);
        window.sliderData.push(values);
    }, 1000); // 1 times per second

    audio.onended = function () {
        window.listeningDuration = Date.now() - window.listeningDurationStartTime; // Capture listening duration
        clearInterval(window.intervalId);

        // Define a function to handle retries
        function handleSaveRetry() {
            window.saveData(function(success) {
                if (success) {
                    clearQuestionnaireForm(); // Clear the form before showing the overlay
                    document.getElementById('questionnaireOverlay').style.display = 'flex';
                    document.getElementById('questionnaireOverlay').scrollTo({top: 0});
                    window.questionnaireDurationStartTime = Date.now(); // Start the timer for questionnaire duration
                } else {
                    // Show retry modal again if it fails
                    showRetryModal(handleSaveRetry);
                }
            });
        }

        // Initial call to save data
        handleSaveRetry();

    };

};

// Function to clear the questionnaire form
window.clearQuestionnaireForm = function() {
    let form = document.getElementById('questionnaireForm');

    // Reset all radio buttons
    let radioButtons = form.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(radio => {
        radio.checked = false; // Uncheck each radio button
    });

    // Clear the textarea
    let feedbackTextarea = document.getElementById('feedback');
    if (feedbackTextarea) {
        feedbackTextarea.value = ''; // Clear the textarea
    }
}

window.submitQuestionnaire = function(event, retryCount = 0, maxRetries = 3) {
    window.questionnaireDuration = Date.now() - window.questionnaireDurationStartTime; // Capture questionnaire duration
    event.preventDefault();

    // Serialize the form data and add the current track as 'current_section'
    let formData = $(event.target).serializeArray(); // Serialize form data

    // Append currentTrack as 'current_section' to the formData array
    formData.push({ name: 'current_section', value: 'instruction' });
    formData.push({ name: 'section_name', value: 'track_' + (window.currentTrack + 1) });
    formData.push({ name: 'track_index', value: (window.currentTrack) });
    formData.push({ name: 'track_index_next', value: (window.currentTrack + 1) });
    formData.push({ name: 'reading_duration', value: window.readingDuration }); // Send reading duration
    formData.push({ name: 'questionnaire_duration', value: window.questionnaireDuration }); // Send questionnaire duration
    formData.push({ name: 'listening_duration', value: window.listeningDuration }); // Send listening duration
    formData.push({ name: 'starting_duration', value: window.startingDuration }); // Send listening duration

    // Send the data to save_response.php using an AJAX POST request
    $.ajax({
        url: '../php/save_response.php',
        type: 'POST',
        data: formData,
        success: function(response) {
            console.log('Form data saved successfully:');
            proceedToNextTrack();
        },
        error: function(xhr, status, error) {
            console.error('Error saving form data:', error);
            // Pass the retry function specific to submitting the questionnaire
            showRetryModal(function() {
                submitQuestionnaire(event); // Retry submitting the questionnaire
            });
        }
    });
};

function proceedToNextTrack() {
    document.getElementById('questionnaireOverlay').style.display = 'none';
    let startButton = document.getElementById('startsong');
    startButton.style.visibility = "visible";
    window.currentTrack++;
    window.loadTrack(window.currentTrack);
}



window.saveData = function(callback, retryCount = 0, maxRetries = 2) {
    let dataToSend = {
        sliderData: window.sliderData,
        currentTrack: window.currentTrack + 1
    };

    let xhr = new XMLHttpRequest();
    xhr.open("POST", "../php/save_experiment_data.php", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.onload = function () {
        if (xhr.status === 200) {
            console.log('Data saved successfully.');
            callback(true);
        } else {
            console.error('Error saving data: ' + xhr.status);
            if (retryCount < maxRetries) {
                console.log(`Retrying... Attempt ${retryCount + 1}`);
                window.saveData(callback, retryCount + 1);
            } else {
                callback(false);
            }
        }
    };
    xhr.onerror = function () {
        console.error('Network error. Retrying...');
        if (retryCount < maxRetries) {
            setTimeout(() => window.saveData(callback, retryCount + 1), 1000); // Retry after 2 seconds
        } else {
            callback(false);
        }
    };
    xhr.send(JSON.stringify(dataToSend));
};



