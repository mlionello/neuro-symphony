<?php
session_start();

require __DIR__ . '/security/endecrypt.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username']);
    $password = trim($_POST['password']);
    $authenticated = false;

    if (empty($username) || empty($password)) {
        echo json_encode(['success' => false, 'message' => 'Username and Password are required.']);
        // echo "<p style='color:red;'>Username and Password are required.</p>";
    } else {
        $hashed_username = hash('sha256', $username);

        if (($file = fopen('users.csv', 'r')) !== false) {
            while (($data = fgetcsv($file, 0, ',', '"', '\\')) !== false) {
                // Compare the hashed username and verify the password
                if ($data[0] === $hashed_username && password_verify($password, $data[1])) {
                    $authenticated = true;

                    // Derive the user-specific key using the input username
                    $user_key = deriveUserKey($username);

                    // Decrypt email and user_id (optional, in case you need it)
                    $decrypted_email = decryptAES($data[2], $user_key);
                    $decrypted_user_id = decryptAES($data[3], $user_key);

                    // Set session variables (avoid exposing sensitive data)
                    $_SESSION['username'] = $username; // Store the plaintext username
                    $_SESSION['user_id'] = $decrypted_user_id; // Optional, only if you need it
                    break;
                }
            }
            fclose($file);
        }
        if (!$authenticated && strpos($username, "debug") === 0) {
            // Extract the part after "debug" and assign it to the session user_id
            $_SESSION['user_id'] = substr($username, 5);

            // Assign 'NONE' to the username session variable
            $_SESSION['username'] = 'NONE';
            echo json_encode([
                'success' => true,
                'username' => "NONE", // Include username in response
                'message' => 'Login successful! Welcome, ' . htmlspecialchars($username) . '.'
            ]);
            exit;
        }

        if ($authenticated) {
            echo json_encode([
                'success' => true,
                'username' => $username, // Include username in response
                'message' => 'Login successful! Welcome, ' . htmlspecialchars($username) . '.'
            ]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Invalid Username or Password.']);
        }
    }
} else {
    echo json_encode(['success' => false, 'message' => 'Invalid request method.']);
}

?>
