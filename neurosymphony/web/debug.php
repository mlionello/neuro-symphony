<?php
session_start();

header('Content-Type: text/plain'); // Set content type for raw text display

if (!empty($_SESSION)) {
    echo "==== SESSION VARIABLES ====\n";
    foreach ($_SESSION as $key => $value) {
        echo htmlspecialchars($key) . ": " . htmlspecialchars(print_r($value, true)) . "\n";
    }
} else {
    echo "No session variables are set.";
}
?>
