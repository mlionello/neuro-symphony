<?php
session_start();

header('Content-Type: application/json'); // Ensure that the response is always in JSON format

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $token = $_POST['token'] ?? '';
    $username = $_POST['username'] ?? '';
    $newPassword = $_POST['newPassword'] ?? '';

    if (empty($newPassword) || empty($token) || empty($username)) {
        echo json_encode(['success' => false, 'content' => 'Invalid request.']);
        exit;
    }

    // Define paths for files
    $file_path = '../users.csv';
    $temp_path = 'temp.csv';
    $isUpdated = false;
    $found = false;

    // Open the original file for reading
    if (($handle = fopen($file_path, 'r')) !== false) {
        // Create a temporary file for writing
        $temp_file = fopen($temp_path, 'w');

        while (($data = fgetcsv($handle)) !== false) {
            if (hash('sha256', $username) === $data[0] && $token === $data[1]) {
                // Verify the token and update the password
                $data[1] = password_hash($newPassword, PASSWORD_DEFAULT); // Replace token with new hashed password
                $found = true;
            }
            fputcsv($temp_file, $data);
        }

        fclose($handle);
        fclose($temp_file);

        // Replace old file with new data if the username and token matched
        if ($found) {
            rename($temp_path, $file_path);
            $isUpdated = true;
        } else {
            unlink($temp_path); // Delete the temp file if no update occurred
        }
    }

    if ($isUpdated) {
        echo json_encode(['success' => true, 'content' => 'Your password has been reset successfully.']);
    } else {
        echo json_encode(['success' => false, 'content' => 'Invalid token or username. Please try the reset link again.']);
    }

} else {
    echo json_encode(['success' => false, 'content' => 'Invalid request method.']);
}
?>
