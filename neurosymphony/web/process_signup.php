<?php
session_start();

require __DIR__ . '/security/endecrypt.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username']);
    $password = trim($_POST['password']);
    $email = trim($_POST['email']);
    $user_id = $_SESSION['user_id'] ?? bin2hex(random_bytes(8)); // Random user_id if not set

    if (empty($username) || empty($password)) {
        echo json_encode(['success' => false, 'message' => 'Username and Password are required.']);
    } else {

        if (isPasswordCompromised($password)) {
            echo json_encode(['success' => false, 'message' => 'Password is too weak. Please choose another.']);
        } else {

            // 1. Hash the username to anonymize it in the system
            $hashed_username = hash('sha256', $username); // Irreversible hash of the username

            if (($file = fopen('users.csv', 'r')) !== false) {
                while (($data = fgetcsv($file, 0, ',', '"', '\\')) !== false) {
                    // Compare the hashed username and verify the password
                    if ($data[0] === $hashed_username) {
                        echo json_encode(['success' => false, 'message' => 'Username already registered.']);
                        exit;
                    }
                }
                fclose($file);
            }

            // 2. Derive the user-specific encryption key from the username
            $user_key = deriveUserKey($username);

            // 3. Encrypt the email and user ID with the user-specific key
            $encrypted_email = encryptAES($email, $user_key);
            $encrypted_user_id = encryptAES($user_id, $user_key);

            // 4. Hash the password (never encrypt it)
            $hashed_password = password_hash($password, PASSWORD_DEFAULT);

            // 5. Store anonymized data in CSV (username hash, password hash, encrypted email, encrypted user_id)
            $file = fopen('users.csv', 'a');
            fputcsv($file, [$hashed_username, $hashed_password, $encrypted_email, $encrypted_user_id], ',', '"', '\\');
            fclose($file);
            echo json_encode(['success' => true, 'message' => 'Signup successful! Your data is securely anonymized. You can now log in.']);
        }
    }
} else {
    echo json_encode(['success' => false, 'message' => 'Invalid request.']);
}


function isPasswordCompromised($password) {
    // Step 1: Hash the password using SHA-1
    $sha1Hash = strtoupper(sha1($password)); // Convert to uppercase as required by HIBP
    $prefix = substr($sha1Hash, 0, 5); // First 5 characters of the hash
    $suffix = substr($sha1Hash, 5); // Remaining part of the hash

    // Step 2: Query the Have I Been Pwned API
    $url = 'https://api.pwnedpasswords.com/range/' . $prefix;

    // Use cURL to get the response from the HIBP API
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    curl_setopt($ch, CURLOPT_USERAGENT, 'YourAppName/1.0'); // Custom user agent
    $response = curl_exec($ch);
    curl_close($ch);

    // Check if the response was successful
    if ($response === false) {
        return false; // If we can't check, assume the password is safe
    }

    // Step 3: Check if the suffix appears in the API response
    $lines = explode("\n", $response);
    foreach ($lines as $line) {
        list($hashSuffix, $count) = explode(':', $line);
        if ($hashSuffix === $suffix) {
            // The password is compromised
            return true;
        }
    }

    // The password is not found in the breach database
    return false;
}
?>
