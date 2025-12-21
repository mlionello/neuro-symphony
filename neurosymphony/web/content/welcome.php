<?php
// assign to the user the descriptors categories

$_SESSION['step'] = 'welcome';

ob_start(); // Start output buffering


if (isset($_SESSION['lang']) && $_SESSION['lang'] == "ita") {
    echo '<h1>Benvenuto/a!</h1>
    <p>Prima di procedere, ti preghiamo di leggere attentamente le seguenti istruzioni.</p>
    <p>
        In questo esperimento, ti verrà chiesto di ascoltare musica sinfonica e valutare diversi fattori.
        L\'intera procedura richiederà circa 40 minuti del tuo tempo e ti chiediamo di completarla
        in un\'unica sessione ininterrotta evitando possibili distrazioni e interruzioni.
        Le <b>cuffie sono essenziali</b> per questo esperimento; le risposte raccolte utilizzando
        sistemi diversi dalle cuffie non saranno incluse nella nostra analisi.
    </p>
    <p>
        L\'ascolto consiste in un intero brano sinfonico suddiviso in 4 movimenti. Durante l\'ascolto di ciascun movimento
        ti verranno mostrati 6 bottoni, ciascuno in riferimento a un particolare aspetto dell\'esperienza.
        Ti verrà richiesto di interagire con i bottoni ogni volta che percepirai un cambiamento nella musica.
        Ciascuno dei 4 movimenti è preceduto da una breve descrizione che dovrai leggere con attenzione.
        Al termine di ciascun movimento ti verranno poste delle domande su quanto appena ascoltato e sulla tua esperienza.
    </p>
    <p>
        I dati saranno elaborati e pubblicati in forma anonima, in conformità con le normative e non sarà possibile in alcun modo risalire alla tua identità tramite le risposte che fornirai.
    </p>
    ';
} else {
    echo '<h1>Welcome!</h1>
    <p>Before proceeding, please read the following information carefully.</p>
    <p>
        In this experiment, you will be asked to listen to symphonic music and evaluate several factors.
        The entire experiment will take about 40 minutes. As a participant, you are asked to complete the experiment
        in a single uninterrupted session. Before starting, please make sure you can dedicate the next 40 minutes to
        this task without distractions or possible interruptions. To avoid interruptions, it is recommended that you set your phone
        to airplane mode. Headphones are essential for this experiment; responses collected using
        external speakers or laptops will not be included in our analysis.
    </p>
    <p>
        During the experiment, you will be asked multiple-choice questions regarding demographic sampling,
        your mood, and your musical experience. At the end of these questionnaires,
        the listening instructions will be repeated, and you will be provided with a 10-second audio sample to adjust the volume to your preference.
    </p>
    <p>The listening phase consists of an entire symphonic piece divided into 4 movements. During each movement,
        you will be presented with 4 sliders, each referring to a particular aspect of the listening experience.
        You will be asked to interact with the sliders whenever you perceive a change in your listening experience.
        Each of the 4 movements will be preceded by a brief description that you should read carefully,
        and at the end of each movement, you will be asked questions about to what you just listened.
        The experiment concludes with a short series of questions about the overall listening experience.
    </p>
    <p>
        The data will be processed and published anonymously, in compliance with XXXX regulations.
    </p>
    ';
}
?>
<form class="submit-and-proceed" method="post">
    <input type="hidden" name="current_section" value="welcome">
    <button type="submit"><?php echo ($_SESSION['lang'] == "eng") ? 'Next' : 'Avanti' ?></button>
</form>
<?php
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>


