<?php
session_start(); // Start or resume the session

// Ensure the user has a session and an ID
if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'No user session found.']);
    exit;
}

$userId = $_SESSION['user_id'];
$fileName = $_SESSION['user_file_path'];

if (!isset($_SESSION['lang'])) {
    $_SESSION['lang'] = "ita";
}

$directory = dirname($fileName);
// Check if the directory exists, and create it if it doesn't
if (!is_dir($directory)) {
    mkdir($directory, 0770, true); // Creates the directory with recursive permissions
}


// Check if data was sent via POST
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Retrieve data from POST
    $data = $_POST;
    $exp_id = $_SESSION['experiment_id'];
    $step = $data["current_section"]; // during experiments this needs to remain 'instruction'

    if (isset($_SESSION['track_index'])) {
        $_SESSION['track_index']=$data["track_index_next"];
    }

    // Initialize an array to hold the response data
    $responses = [];

    // Check if the JSON file already exists
    if (file_exists($fileName)) {
        // Read the existing data
        $existingData = file_get_contents($fileName);
        $responses = json_decode($existingData, true) ?: []; // Decode or use an empty array
    }

    if (isset($data['track_index_next'])) {
        $responses[$exp_id]['track_index'] = $data['track_index_next'];
    }

    // Save the new response data
    if (isset($data['section_name'])) {
        $responses[$exp_id][$data['section_name']] = $data;
    } else {
        $responses[$exp_id][$step] = $data;
    }
    $responses[$exp_id]['step'] = $step;

    // Check if the current step is 'welcome' and save the entire session
    if ($step === 'welcome') {
        // Save all session data to the JSON excluding specific fields
        $sessionData = $_SESSION;
        // Exclude 'username' field
        unset($sessionData['username']);

        $responses[$exp_id]['session_data'] = $sessionData;
        $responses['experiment_started_time'] = time();
        $responses['experiment_id'] = $exp_id;
    }

    if ($step === 'goldsmi2' || $step === 'post_experiment') {
        unset($_SESSION['step']);
        $responses[$exp_id]['status'] = 'done';
        $responses[$exp_id]['step'] = 'done';
        if ( $step === 'post_experiment'){
            $responses['nb']['completed'] = $responses['nb']['completed'] + 1;
            $responses['completed_exp_id'][] = $exp_id;
            $responses['experiment_started_time'] = 0;
        }
    }

    // Save the updated responses back to the JSON file
    if (file_put_contents($fileName, json_encode($responses, JSON_PRETTY_PRINT))) {
        if ( $step === 'post_experiment'){
            // Respond with a success message
            $log_row = [
                $_SESSION['user_id'],           // User ID
                time(),                         // Current timestamp
                '',                             // Experiment ID that started (empty)
                $_SESSION['experiment_id'],     // Experiment ID that finished
                $_SESSION['assigned_condition'] // Assigned condition
            ];

            try {
                $file = fopen($_SESSION['experiment_log'], 'a'); // Open log.csv in append mode
                if ($file !== false) {
                    fputcsv($file, $log_row, ',', '"', '\\'); // Add the row to the CSV file
                    fclose($file); // Close the file
                } else {
                    throw new Exception("Unable to open log file.");
                }
            } catch (Exception $e) {
                error_log("Error logging to CSV: " . $e->getMessage());
            }
            echo json_encode(['status' => 'success', 'message' => 'Response saved successfully.']);
        }
    } else {
        // Respond with an error if unable to write the file
        echo json_encode(['status' => 'error', 'message' => 'Failed to save response.']);
    }

} else {
    // Respond with an error if the request method is not POST
    echo json_encode(['status' => 'error', 'message' => 'Invalid request method.']);
}
?>
