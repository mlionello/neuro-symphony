<?php

header('Content-Type: application/json');
$_SESSION['step'] = 'post_experiment';
$debug = $_SESSION['debug'];

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}

ob_start(); // Start output buffering
echo '
<input type="hidden" id="debugContainer" value="'.(bool)$debug.'">
<script>
        var debug = <?php echo json_encode((bool)$debug); ?>;
</script>
';

if (isset($_SESSION['lang']) && $_SESSION['lang'] == "eng") {
echo '
    <script src="../js/questionnaire_header_radios.js"></script>
    <h1>Last Questions!</h1>
    <form id="form-post_experiment.php" class="submit-and-proceed" method="post">
        <input type="hidden" name="current_section" value="post_experiment">
        <p>By considering the whole listening experience, to what extend do you dis/agree with the following statements from 1 (totally disagree) to 9 (totally agree)?:
        <div id="post_experiment_setquestion1"></div>
        <br><br>
        <label for="comments">Any additional comments?</label>
        <br>
        <textarea id="comments" name="comments" rows="4" cols="50"></textarea><br><br>

        <button type="submit">Submit</button>
    </form>
    <script src="../js/post_experiment.js" defer></script>
';
} else {
echo '
    <script src="../js/questionnaire_header_radios.js"></script>
    <h1>Ultime Domande!</h1>
    <form id="form-post_experiment.php" class="submit-and-proceed" method="post">
        <input type="hidden" name="current_section" value="post_experiment">
        <p>Considerando l\'intera esperienza di ascolto:
        <div id="post_experiment_setquestion1"></div>
        <br><br>
        <label for="comments">Se vuoi lascia un commento generale sull\'esperimento</label>
        <br>
        <textarea id="comments" name="comments" rows="4" cols="50"></textarea><br><br>

        <button type="submit">Invia</button>
    </form>
    <script src="../js/post_experiment.js" defer></script>
';


}
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>
