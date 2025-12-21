<?php

header('Content-Type: application/json');
$debug = $_SESSION['debug'];

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}

$_SESSION['step'] = 'experiment';

if (!isset($_SESSION['track_index'])) {
    $_SESSION['track_index']=0;
}

// Ensure the random words are available in the session
if (!isset($_SESSION['labels']) || count($_SESSION['labels']) < 4) {
    echo json_encode(['error' => 'Required labels are missing. Please restart the experiment.']);
    http_response_code(500); // Internal Server Error
    exit;
}

// Ensure the random words are available in the session
$wait_loading_button_text = 'Please wait, loading song...';
$play_button_text = "Start";
$track_text = "Track";
$I_have_read_it = "I have read it";
$track_feedback = 'Track Feedback:';
$submit_button = 'Next';

if (isset($_SESSION['lang']) && $_SESSION['lang'] == "ita") {
    $wait_loading_button_text = "Caricamento audio, attendere...";
    $play_button_text = "Inizia";
    $track_text = "Movimento";
    $I_have_read_it = "Ho letto";
    $track_feedback = 'Feedback:';
    $submit_button = 'Continua';
}

// Assign the random labels to the sliders
$labels = $_SESSION['labels'];

// Combine audio paths and descriptions based on track number
$tracks = [];
foreach ($_SESSION['audioPaths'] as $pathIndex => $path) {
    $description = $_SESSION['descriptions'][$pathIndex];
    $tracks[] = [
        'file' => $path['path'],
        'description' => $description['description']
    ];
}

$debug = $_SESSION['debug'];

// Prepare HTML content to be returned
ob_start(); // Start output buffering
?>
<input type="hidden" id="debugContainer" value="<?php echo (bool)$debug; ?>">
<script src="../js/questionnaire_header_radios.js"></script>

<!-- Retry Modal -->
<div id="retryModal" style="display:none; position:fixed; left:0; top:0; width:100%; height:100%; background-color:rgba(0,0,0,0.5); z-index:100000;">
    <div style="background-color:#fff; margin:15% auto; padding:20px; border-radius:5px; width:80%; max-width:400px; text-align:center;">
        <p>Failed to save data. Please check your internet connection and try again.</p>
        <button id="retryButton">Retry</button>
        <button onclick="closeRetryModal()">Cancel</button>
    </div>
</div>


<div id="wait_loading_button_text" style="display:none;"><?php echo $wait_loading_button_text; ?></div>
<div id="play_button_text" style="display:none;"><?php echo $play_button_text; ?></div>
<div id="track_text" style="display:none;"><?php echo $track_text; ?></div>

<div id="tracksData" style="display:none;"><?php echo json_encode($tracks); ?></div>
<div id="tracks_index" style="display:none;"><?php echo $_SESSION['track_index']; ?></div>

<div class="overlay" id="descriptionOverlay" style="display: none;">
    <h1 id="trackTitle"></h1>
    <p id="trackDescription"></p>
    <button onclick="close_description()"><?php echo $I_have_read_it; ?></button>
</div>

<div class="overlay" id="questionnaireOverlay" style="display: none;">
    <h2><?php echo $track_feedback; ?></h2>
    <form id="questionnaireForm" onsubmit="submitQuestionnaire(event)">
        <div class="likert-question" id="likert_question_track">
        </div><br>
        <button type="submit"><?php echo $submit_button; ?></button>
    </form>
</div>

<div class="experiment-container">
    <div class="sliders-container">
        <button id="startsong" onclick="startExperiment()" style="margin-bottom: 40px;"><?php echo $play_button_text; ?></button><br>
        <div style="align-self:center; padding: 0 20px 0 20px; display: grid; grid-template-columns: 5fr 1fr; width: fit-content; margin: auto;">
        <?php foreach ($labels as $index => $label): ?>
                <label class="label" for="button<?php echo $index; ?>"><?php echo $label[0]; ?></label>
                <button id="button<?php echo $index; ?>" class="toggle-button" value="0" onclick="toggleButtonState(this, <?php echo $index; ?>)">Off</button>
        <?php endforeach; ?>
        </div>
    </div>

    <audio id="audioPlayer" src=""></audio>
    <div id="trackCounter" class="track-counter"><?php echo $track_text; ?> 1/<?php echo count($tracks); ?></div>
</div>
<div style="display:none">
    <form id="form-instruction.php" class="submit-and-proceed" method="post">
        <input type="hidden" name="current_section" value="experiment">
        <button id="finish_experiment" type="submit"></button>
    </form>
</div>
<script>
        debug = <?php echo json_encode((bool)$debug); ?>;
</script>
<script src="../js/feedback_track.js"></script>
<script src="../js/experiment.js?1500"></script>
<script>
    loadTrack(window.currentTrack);
</script>

<?php
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>
