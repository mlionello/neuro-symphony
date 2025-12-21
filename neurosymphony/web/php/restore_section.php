<?php

session_start();
error_reporting(E_ALL);
ini_set('display_errors', 1);

if (!isset($_SESSION['user_id'])) {
    echo "User ID not set.";
    exit;
}


$file_path = __DIR__ . '/../content/' . $_POST['section'] . '.php';
include $file_path;

?>
