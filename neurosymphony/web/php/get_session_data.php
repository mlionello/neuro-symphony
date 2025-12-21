<?php
session_start();
header('Content-Type: application/json');

// Check if session variables are set and return them
$response = [
    'user_id' => $_SESSION['user_id'],
    'descriptions_class' => $_SESSION['descriptions_class'],
    'step' => $_SESSION['step'],
];

echo json_encode($response);
exit;
?>
