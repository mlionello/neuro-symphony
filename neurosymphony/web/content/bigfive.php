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
$_SESSION['step'] = 'bigfive';

ob_start(); // Start output buffering
?>
<?php
echo '<input type="hidden" id="debugContainer" value="'.(bool)$debug.'">
        <div id="trackCounter" class="track-counter">';
echo ($_SESSION["lang"] == "ita") ? "questionario " : "questionnaire ";
echo '2/4</div>';
?>

<h2>Tratti caratteriali</h2>

<p>Di seguito trovi elencate delle caratteristiche che possono riguardarti o meno. Per esempio, sei d'accordo di essere una persona a cui piace passare del tempo con gli/le altri/e?
Ti chiediamo di indicare quanto tu sei d'accordo o in disaccordo con ciascuna affermazione.</p>
<br>
Mi vedo come una persona che...
<form id="bigfive-form" class="submit-and-proceed" method="post">
    <input type="hidden" name="current_section" value="bigfive">

<div id="questions-containerbigfive" class="form_container_fixed_header"></div>
    <button type="submit">Invia e continua</button>
</form>


<script>
        var debug = <?php echo json_encode((bool)$debug); ?>
</script>
<script src="../js/questionnaire_header_radios.js" defer></script>
<script src="../js/bigfive.js" defer></script>
<?php
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>

