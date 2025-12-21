<?php
session_start();

// Get the user ID from the session
$userId = isset($_SESSION['user_id']) ? $_SESSION['user_id'] : null;

// Check if user ID is set
if (!$userId) {
    http_response_code(400);
    echo json_encode(['error' => 'User ID not found in session.']);
    exit;
}

// Retrieve JSON data sent from JavaScript
$inputData = file_get_contents('php://input');
$data = json_decode($inputData, true);

// Validate the received data
if (!isset($data['sliderData']) || !is_array($data['sliderData']) || empty($data['sliderData'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid or empty slider data received.']);
    exit;
}

if (!isset($data['currentTrack']) || !is_numeric($data['currentTrack'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid or missing current track number.']);
    exit;
}

// Extract slider data and current track from the decoded JSON
$sliderData = $data['sliderData'];
$currentTrack = $data['currentTrack'];

// Define the file path and name
$baseFileName = $_SESSION['usr_directory'] . "/" . $_SESSION['experiment_id'] . "_traccia" . $currentTrack . ".csv";
$directory = dirname($baseFileName);

// Check if the directory exists, and create it if it doesn't
if (!is_dir($directory)) {
    mkdir($directory, 0770, true);
}

$uniqueFileName = $baseFileName;
$counter = 1;

// Extract file information
$fileInfo = pathinfo($baseFileName);
$baseName = $fileInfo['dirname'] . '/' . $fileInfo['filename'];
$extension = isset($fileInfo['extension']) ? '.' . $fileInfo['extension'] : '';

// Loop to ensure unique file name
while (file_exists($uniqueFileName)) {
    $uniqueFileName = $baseName . '_' . $counter . $extension;
    $counter++;
}

// Attempt to open the file for writing
$file = fopen($uniqueFileName, 'w');

if ($file === false) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to open file for writing.']);
    exit;
}

chmod($uniqueFileName, 0770);  // Set file permissions to 770

// Write each row of the slider data to the CSV file
foreach ($sliderData as $row) {
    // Ensure each row is an array before writing
    if (is_array($row)) {
        fputcsv($file, $row);
    }
}

// Close the file after writing all data
fclose($file);

// Send a success response back to the JavaScript
http_response_code(200);
echo json_encode(['success' => 'Data saved successfully.']);
?>
