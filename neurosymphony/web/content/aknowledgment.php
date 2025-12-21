<?php

header('Content-Type: application/json');
$_SESSION['step'] = 'aknowledgment';

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}

ob_start(); // Start output buffering
if (isset($_SESSION['lang']) && $_SESSION['lang'] == "eng") {
    echo '
        <h1>Thank You for Participating!</h1>
        <p>Your responses have been recorded. We would like to sincerely thank you for your time and effort!</p>
        ';
} else {
    echo '
    <h1>Grazie per aver partecipato!</h1>
    <p>Le tue risposte sono state salvate. Ti vogliamo sinceramente ringraziare per il tuo tempo e impegno!</p><br>
    <p>Ti è piaciuto l\'esperimento? Visita <a href="https:///www.neuro-symphony.com">www.neuro-symphony.com</a>
    per rimanere in contatto per ulteriori esperimenti!</p>
    ';
}
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>
