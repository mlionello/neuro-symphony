<?php

session_start();
error_reporting(E_ALL);
ini_set('display_errors', 1);

if (!isset($_SESSION['user_id'])) {
    echo "User ID not set.";
    exit;
}

$current_section = $_POST['section'];

$valid_sections = ['terms', 'demographics', 'bigfive', 'goldsmi1',  'goldsmi2'];

if (!in_array($current_section, $valid_sections)) {
    http_response_code(400);
    echo "Invalid request. Please return to the starting page.";
    exit;
}

// Logic to determine the next section based on the current section
$next_section_key = array_search($current_section, $valid_sections);
$next_section = $valid_sections[$next_section_key + 1] ?? null;

if ($next_section) {
    $file_path = __DIR__ . '/../content/' . $next_section . '.php';
    if (file_exists($file_path)) {
        include $file_path;
    } else {
        http_response_code(404); // Not Found
        echo "Section file not found: " . htmlspecialchars($file_path);
    }
} else {
    // All sections completed, load the dashboard
    include '../dashboard.php'; // Load the dashboard
}
?>
