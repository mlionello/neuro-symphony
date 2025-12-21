<?php

header('Content-Type: application/json');

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}
$_SESSION['step'] = 'instruction';

// Ensure the random words are available in the session
if (!isset($_SESSION['labels']) || count($_SESSION['labels']) < 4) {
    echo json_encode(['error' => 'Required labels are missing. Please restart the experiment.']);
    http_response_code(500); // Internal Server Error
    exit;
}

// Assign the random labels to the sliders
$labels = $_SESSION['labels'];

// Ensure the random words are available in the session
$play_button_text = "Start Example";
$stop = "I am happy with the volume";
$wait_loading_button_text = 'Please wait, loading song...';
$wait_start_exp_button_text = 'Please start example audio first';

if (isset($_SESSION['lang']) && $_SESSION['lang'] == "ita") {
    $play_button_text = "Riproduci Esempio";
    $stop = "Ho impostato e sono soddisfatto con il volume dell'audio";
    $wait_loading_button_text = "Caricamento audio, attendere...";
    $wait_start_exp_button_text = 'Per favore prima l\'audio di esempio';
}

// Prepare HTML content to be returned
ob_start(); // Start output buffering
?>
<?php
if (isset($_SESSION['lang']) && $_SESSION['lang'] == "eng") {
echo '
    <h1>Instructions</h1>
    <p>You are ready to start the experiment! You will listen to 4 movements of a symphony: each movement will be accompanied by a brief textual description to guide you through the listening. Please read the description carefully; you will be asked to recall part of that after the listening.</p>
    <p>During the listening, 4 sliders will be displayed. Each slider is associated with a label. You are asked to interact with these sliders to keep track of the emotion, sensation, or perceptions they indicate. Move the sliders in the desired direction as soon as you perceive a change in the indicated component.</p>
    <p>After the listening of each track, you will be asked to rate some specific aspects of the track and give some replies according to the description you were initially given.</p>
    <p style="padding-top: 20px">Here is an example of the listening task: click on start song and adjust now the volume at your desired level:</p>
';
} else {
echo '
    <h1>Istruzioni</h1>
    <p>Sei pronto per iniziare l\'esperimento! Ascolterai 4 movimenti di una sinfonia: ogni movimento sarà accompagnato da una breve descrizione testuale per guidarti durante l\'ascolto. Ti preghiamo di leggere attentamente la descrizione; ti verrà richiesto di rispondere a delle domande relative alla descrizione dopo il termine dell\'ascolto.</p>
    <p>Durante l\'ascolto, verranno visualizzati 6 bottoni. Ogni bottone è associato a un\'etichetta:</p>
    <ul>
    <li>Ti chiediamo di interagire con questi bottoni per descrivere in ogni momento quello che <b>stai provando</b> sulla base del brano che stai ascoltando;</li>
    <li>Attiva e disattiva ciascun bottone per riportare l\'inizio o la fine di uno stato emotivo <b>ogni volta che ne percepisci uno</b>.</li>
    <li>Ad esempio, se in un dato momento percepisci che stai provando tensione, assicurati che il bottone relativo a \'tensione\' sia attivato (\'On\'). Potresti percepire più sensazioni contemporaneamente e dover attivare più bottoni.
    Quando ritieni che una sensazione riferita a un bottone non sia più presente in un certo momento, disattiva quel bottone cliccandoci sopra (\'Off\').</li>
    <li>I dati dei bottoni vengono raccolti in maniera <b>continua</b>, quindi attiva e disattiva i bottoni ogni volta che vuoi pensando alla sensazione percepita in ogni istante.</li>
    <li>Non preoccuparti se le sensazioni cambiano troppo velocemente, o se cambiano più sensazioni nello stesso momento, cerca di interagire con i bottoni mantenendo un ascolto attento alla musica.</li>
    </ul>
    <p>Partendo da uno stato \'Off\' scritto sul bottone, cliccaci sopra per attivare la sensazione specifica e comparirà la scritta \'On\' per specificare che il bottone è attivo.</p>
    <p>Dopo l\'ascolto di ciascun movimento, ti verrà chiesto di valutare alcuni aspetti specifici di quanto ascoltato e di fornire alcune risposte in base alla descrizione che ti è stata inizialmente data.</p>
    <p style="padding-top: 20px">Ecco un esempio di ascolto: <b>indossa le cuffie ora</b>, fai clic su inizia brano e regola ora il volume al livello desiderato:</p>
';
}
?>
<div style="align-self:center; text-align:center; padding: 0 20px 0 20px">
    <button id="startexample" onclick="playAudio()" style="margin-right: 20px"></button>
    <button id="stopexample" onclick="stopAudio()"></button><br>
    <audio id="audioPlayer" src="./audio/Symphony_Fantastique.mp3"></audio>
</div>
<?php echo (isset($_SESSION['lang']) && $_SESSION['lang'] == "eng") ?
    '<p style="padding-top: 20px">These are the sliders you will interact with during the listening:</p>' :
    '<p style="padding-top: 20px">Questi saranno i bottoni con cui interagirai durante l\'ascolto. Leggi attentamente le etichette associate. Puoi provare ad attivarli e disattivarli per prendere confidenza con il compito:</p>';
?>
<div class="experiment-container" style="height:auto">
        <div class="sliders-container">
        <div style="align-self:center; padding: 0 20px 0 20px; display: grid; grid-template-columns: 5fr 1fr; width: fit-content; margin: auto;">
        <?php foreach ($labels as $index => $label): ?>
                <label class="label" for="button<?php echo $index; ?>"><?php echo $label[0]; ?></label>
                <button id="button<?php echo $index; ?>" class="toggle-button" value="0" onclick="toggleButtonState_instruction(this, <?php echo $index; ?>)">Off</button>
        <?php endforeach; ?>
        </div>
        </div>
    </div>
<script>
let buttonStates=[];

function toggleButtonState_instruction(button, index) {
    // Ensure buttonStates array is initialized
    if (typeof buttonStates[index] === 'undefined') {
        buttonStates[index] = false;
    }

    // Toggle the state
    buttonStates[index] = !buttonStates[index];

    button.innerText = buttonStates[index] ? "On" : "Off";
    button.value = buttonStates[index] ? "1" : "0";
    button.style.backgroundColor = buttonStates[index] ? "#0066cc" : "#a8aaac";
    button.style.color = buttonStates[index] ? "white" : "black";

}

ranges_instruction = document.querySelectorAll(".slider");

ranges_instruction.forEach(range => {
    range.addEventListener("input", () => {
        let min = range.min;        // The minimum value of the current slider
        let max = range.max;        // The maximum value of the current slider
        let currentVal = range.value; // The current value of the current slider

        // Calculate the percentage of how much the slider has been filled
        let percentage = ((currentVal - min) / (max - min)) * 100;

        // Update the current slider's background size based on the percentage
        range.style.backgroundSize = percentage + "% 100%";
    });
});
</script>
<?php echo (isset($_SESSION['lang']) && $_SESSION['lang'] == "eng") ?
'<p>You are ready to go! Click on the "Start" button to start the experiment.</p>' :
'<p>Mettiti comodo/a ed evita distrazioni e interruzioni, se possibile metti il cellulare in modalità aereo. Il concerto che ascolterai dura fra i 30 e 40 minuti. L\'esperienza è pensata per essere un momento di ascolto concentrato e coinvolgente. Ricordati che puoi chiudere l\'esperimento in qualsiasi momento. Se dovessi ritrovarti bloccato/a sul  caricamento di una traccia, attendi un minuto, se dovesse persistere il caricamento puoi ricaricare la pagina mantenendo i tuoi progressi.</p>
<p>Sei pronto/a per iniziare l\'esperimento! Clicca su inizia!</p>';
?>
    <form id="form-instruction.php" class="submit-and-proceed" method="post">
        <input type="hidden" name="current_section" value="instruction">
        <button id="startexp" type="submit"></button>
    </form>
    <script>
        audioPlayerexample = document.getElementById('audioPlayer');
        audioPlayerexample.preload = 'auto';
        startexampleButton = document.getElementById('startexample');
        stopexampleButton = document.getElementById('stopexample');
        startexp = document.getElementById('startexp');

        function playAudio() {
            var audio = document.getElementById("audioPlayer");
            audio.play().catch(error => {
                alert("Unable to play audio. Please ensure your browser allows audio playback.");
                console.error("Audio play error:", error);
            });
            startexp.disabled = false;
            startexp.innerText = "<?php echo ($_SESSION['lang'] == "eng") ? 'Start' : 'Inizia'; ?>";
        }

        function stopAudio() {
            var audio = document.getElementById("audioPlayer");
            audio.pause();
            audio.currentTime = 0;
        }

        [startexampleButton, stopexampleButton, startexp].forEach(item => {
            item.disabled = true;
            item.innerText = "<?php echo $wait_loading_button_text; ?>";
        });
        startexp.innerText = "<?php echo $wait_start_exp_button_text; ?>";

        audioPlayerexample.oncanplaythrough = function () {
            // Enable the start button when the audio is ready to play
            startexampleButton.disabled = false;
            stopexampleButton.disabled = false;
            startexampleButton.innerText = "<?php echo $play_button_text; ?>";
            stopexampleButton.innerText = "<?php echo $stop; ?>";
        };
    </script>
<?php
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>

