<?php
header('Content-Type: application/json');

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}
$_SESSION['step'] = 'terms';
// Prepare HTML content to be returned
ob_start(); // Start output buffering
if (isset($_SESSION['lang']) && $_SESSION['lang'] == "ita") {
echo '<h1>Termini e Condizioni</h1>
<form id="terms-form" class="submit-and-proceed" method="post">
    <input type="hidden" name="current_section" value="terms">
    <p>Per favore, leggi attentamente i termini generali dell\'esperimento.
        Se desideri procedere con la partecipazione, accetta i termini e le condizioni dell\'esperimento cliccando
        sul box che trovi qua sotto, altrimenti puoi chiudere la pagina. La partecipazione è volontaria e può
        essere interrotta in qualsiasi momento</p>
        <p> Sono d\'accordo che:
        <ul style="list-style-type:none ">
            <li> lo studio sia condotto secondo le normative vigenti (D. Lgs 196/2003 e UE GDPR 679/2016) in materia di protezione dei dati e che le informazioni personali saranno trattate nei limiti, per le finalità e per la durata previste da tali normative;</li>
            <li> per partecipare allo studio è necessario avere almeno 18 anni;</li>
            <li> la partecipazione allo studio è completamente volontaria ed è possibile interromperla in qualsiasi momento, senza dover fornire alcuna spiegazione;</li>
            <li> i dati saranno raccolti in forma anonima e sarà impossibile identificare il partecipante in alcun modo tramite le informazioni fornite;</li>
            <li> le risposte saranno accessibili solo ai ricercatori della IMT School e saranno utilizzate esclusivamente per fini di ricerca;</li>
            <li> il reclutamento è avvenuto tramite reclutamento a catena (snowball), email o contatto con gli sperimentatori.</li>
        </ul></p>

    <label for="accept">Ho letto e accetto i termini e condizoni:</label>
    <input type="checkbox" id="accept" name="accept" required aria-required="true"><br><br>
    <button type="submit">Procedi</button>
</form>';
} else {
echo '<h1>Terms and Conditions</h1>
<form id="terms-form" class="submit-and-proceed" method="post">
    <input type="hidden" name="current_section" value="terms">
    <p>Please read the terms and conditions carefully. Participation is voluntary and you can withdraw at any time.</p>
    <p> I agree that:
    <ul style="list-style-type:none ">
        <li> that the study is administered according to current rules (D. Lgs 196/2003 and UE GDPR 679/2016) concerning data protection and that your personal information will be processed within the limitations, for the purposes, and for the duration specified by these rules;</li>
        <li> that for taking part to the study you must be at least 18 years old;</li>
        <li> that the participation to the study is completely voluntary and that you can interrupt the survey at any time, without having to provide any explanation;</li>
        <li> that data will be collected anonymously and that it will be impossible to identify you in any way by means of the information provided by you during the survey;</li>
        <li> that your responses will be accessed only by IMT School researchers and used for research purposes only;</li>
        <li> that the recruitment took place through snowball recruitment, email or contact with experimenters.</li>
    </ul></p>
    <label for="accept">I have read and accept the terms:</label>
    <input type="checkbox" id="accept" name="accept" required aria-required="true"><br><br>
    <button type="submit">Submit and Next</button>
</form>';
}

$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>
