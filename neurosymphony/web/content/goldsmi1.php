<?php
header('Content-Type: application/json');
if (isset($_SESSION['debug'])) {
    $debug = $_SESSION['debug'];
} else {$_SESSION['debug']=false; $debug=false;}
$debug = $_SESSION['debug'];

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}
$_SESSION['step'] = 'goldsmi1';

ob_start(); // Start output buffering
?>
<?php
echo '<input type="hidden" id="debugContainer" value="'.(bool)$debug.'">
        <div id="trackCounter" class="track-counter">';
echo ($_SESSION["lang"] == "ita") ? "questionario " : "questionnaire ";
echo '3/4</div>';
?>

<h2>Attitudine musicale 1/2</h2>

<p>Prima di accedere all'esperimento abbiamo bisogno di raccogliere alcune informazioni circa il tuo rapporto con la musica.</p>

<form id="goldsmi-form1" class="submit-and-proceed" method="post">
    <input type="hidden" name="current_section" value="goldsmi1">

<div id="questions-containergoldsmi1" class="form_container_fixed_header"></div>
    <button type="submit">Invia e continua</button>
</form>


<script>
        var debug = <?php echo json_encode((bool)$debug); ?>
</script>
<script src="../js/questionnaire_header_radios.js" defer></script>
<script src="../js/goldsmi1.js" defer></script>
<?php
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>

