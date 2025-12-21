<?php

function deriveUserKey($username) {
    global $global_secret_key;
    $key_path = '/var/secure/keys/neurosymphony_music_context.key';
    $key_path = '/Users/mlionello/neurosymphony_music_context.key';

    // Check if the key file is accessible
    if (!file_exists($key_path) || !is_readable($key_path)) {
        echo "Internal Error: Key file not accessible.";
        exit;
    }

    // Read the key from the file
    $global_secret_key = trim(file_get_contents($key_path));

    // Check if the key is empty
    if (empty($global_secret_key)) {
        echo "Internal Error: Impossible to retrieve decryption key.";
        exit();
    }

    return hash_hmac('sha256', $username, $global_secret_key, true); // 32-byte key for AES-256-CBC
}


function encryptAES($data, $key) {
    $iv = random_bytes(16); // Generate a 16-byte IV
    $encrypted_data = openssl_encrypt($data, 'AES-256-CBC', $key, OPENSSL_RAW_DATA, $iv);
    return base64_encode($iv . $encrypted_data); // Prepend IV to encrypted data
}

function decryptAES($encrypted_data, $key) {
    $decoded_data = base64_decode($encrypted_data);
    $iv = substr($decoded_data, 0, 16); // Extract the first 16 bytes as the IV
    $encrypted_text = substr($decoded_data, 16); // Extract the remaining ciphertext
    $decrypted_data = openssl_decrypt($encrypted_text, 'AES-256-CBC', $key, OPENSSL_RAW_DATA, $iv);
    return $decrypted_data;
}

?>