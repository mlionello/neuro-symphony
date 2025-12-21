<?php
session_start();

require __DIR__ . '/security/endecrypt.php';

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username']);

    if (empty($username)) {
        echo json_encode(['success' => false, 'message' => 'Username is required.']);
        exit;
    }

    $hashed_username = hash('sha256', $username);
    $user_key = deriveUserKey($username); // Derive the key used for decryption

    $file_path = 'users.csv';
    $temp_file_path = 'users_temp.csv';

    if (($file = fopen($file_path, 'r')) !== false) {
        $found = false;
        $data_array = [];

        // Read through the CSV and collect user data
        while (($data = fgetcsv($file, 0, ',', '"', '\\')) !== false) {
            if ($data[0] === $hashed_username) {
                $found = true;
                $reset_token = bin2hex(random_bytes(16)); // Generate a reset token
                $reset_link = "https://neuro-symphony.com/reset_password?token=$reset_token&username=$username";

                // Replace the password with the reset token
                $data[1] = $reset_token;

                // Decrypt email using user-specific key
                $email = decryptAES($data[2], $user_key);

                // Send the reset link via email
                $subject = 'Password Reset Request';
                $message = "Please click on the following link to reset your password: $reset_link";
                $headers = 'From: noreply@neuro-symphony.com' . "\r\n" .
                           'X-Mailer: PHP/' . phpversion();

                mail($email, $subject, $message, $headers);
            }
            $data_array[] = $data;
        }

        fclose($file);

        // Rewrite the CSV with the new data
        if ($found) {
            $file = fopen($temp_file_path, 'w');
            foreach ($data_array as $line) {
                fputcsv($file, $line);
            }
            fclose($file);
            // Replace old CSV with new CSV
            rename($temp_file_path, $file_path);

            echo json_encode(['success' => true, 'message' => 'In the case you provided an email address during the registration, a password reset link has been sent to your email. If you did not receive the email, please wait a couple of minutes and do check the spam folder.']);
        } else {
            echo json_encode(['success' => false, 'message' => 'User not found.']);
        }
    } else {
        echo json_encode(['success' => false, 'message' => 'Could not open user database.']);
    }
} else {
    echo json_encode(['success' => false, 'message' => 'Invalid request method.']);
}
?>
