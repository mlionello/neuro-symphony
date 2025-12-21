<?php
session_start();

// Destroy the entire session
session_unset();
session_destroy();

// Return a JSON response
echo json_encode(['success' => true, 'message' => 'Logged out successfully.', 'refresh' => true]);

?>
