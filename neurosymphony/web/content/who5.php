<?php
header('Content-Type: application/json');
$debug = $_SESSION['debug'];

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}
$_SESSION['step'] = 'who5';

ob_start(); // Start output buffering

echo '<input type="hidden" id="debugContainer" value="'.(bool)$debug.'">
      <div id="trackCounter" class="track-counter">';
echo ($_SESSION["lang"] == "ita") ? "questionario " : "questionnaire ";
echo '1/1</div>';

if (isset($_SESSION['lang']) && $_SESSION['lang'] == "eng") {
    echo '
    <h2>Well-being Index</h2>
    <form id="who5-form" class="submit-and-proceed" method="post">
        <input type="hidden" name="current_section" value="who5">
        <div id="questions-containerwho5></div>
        <button type="submit">Submit and Next</button>
    </form>';
} else {
    echo '
    <h2>Stato di benessere (OMS)</h2>
    <p>Nelle ultime due settimane... </p>
    <form id="who5-form" class="submit-and-proceed" method="post">
        <input type="hidden" name="current_section" value="who5">
        <div id="questions-containerwho5"></div>
        <button type="submit">Successivo</button>
    </form>';
}

echo '<script src="../js/questionnaire_header_radios.js"></script>
        <script src="../js/who5.js"></script>';

$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>

