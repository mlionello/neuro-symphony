<?php

header('Content-Type: application/json');
$_SESSION['step'] = 'cannotproceed';

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}

ob_start(); // Start output buffering
if (isset($_SESSION['lang']) && $_SESSION['lang'] == "eng") {
    echo '
        <h1>Thank You for Participating!</h1>
        <p>Unfortunately, the inclusion criteria for our study do not allow us to proceed with the experiment. Anyway, we would still like to sincerely thank you for your availability!</p>
        ';
} else {
    echo '
    <h1>Grazie la tua partecipazione!</h1>
    <p>Purtroppo i criteri di inclusione del nostro studio non ci permettono di procedere con l\'esperimento, ti vogliamo comunque sinceramente ringraziare per la disponibilità!</p>
    ';
}
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>
