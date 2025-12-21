<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

header('Content-Type: application/json');

$user_id = $_SESSION['user_id']; // Fallback to 'guest' if user_id is not set

// Generate the path for the user's JSON file
$_SESSION['user_file_path'] = __DIR__ . "/userdata/user_{$user_id}/{$user_id}.json";
$_SESSION['usr_directory'] = dirname($_SESSION['user_file_path']);
$_SESSION['overall_consts'] =  __DIR__ . '/data/framework.json';
$_SESSION['experiment_log'] =  __DIR__ . '/userdata/experiments_log.csv';
// $_SESSION['exp_conditions'] =  __DIR__ . '/data/shuffled_combinations.csv'; moved to exp framework json
$exp_id_questionnaires = 'demographics_and_GMSI';

if (!isset($_SESSION['lang'])) {
    $_SESSION['lang'] = "ita";
}

// Ensure userdata directory exists
if (!is_dir($_SESSION['usr_directory'])) {
    mkdir($_SESSION['usr_directory'], 0777, true);
}

// Check if the file exists; if not, create it with default content
if (!file_exists( $_SESSION['user_file_path'])) {
    $default_content = [
        $exp_id_questionnaires => [
            'status' => 'not done',
        ],
        'nb' => [
            'completed' => 0
        ],
        'completed_exp_id' => []
    ];
    file_put_contents( $_SESSION['user_file_path'], json_encode($default_content, JSON_PRETTY_PRINT));
}

// Load the JSON file content
$user_data = json_decode(file_get_contents( $_SESSION['user_file_path']), true);
$all_data = json_decode(file_get_contents( $_SESSION['overall_consts']), true);

$preliminary_done = $user_data[$exp_id_questionnaires]['status'] === 'done';

$unique_exp_ids = array_unique($user_data['completed_exp_id']);
$nb_exp_completed = count($unique_exp_ids);

$nb_total_exp = $all_data['nb']['experiments'];
if (!$preliminary_done) {
    $_SESSION['experiment_id'] = $exp_id_questionnaires;
}


$listened_to = [];
foreach ($unique_exp_ids as $expid_tmp){
    $listened_to[] = $all_data[$expid_tmp]['title'] ?? 'missing';
}

ob_start(); // Start output buffering
?>

<h2>Dashboard</h2>
<p style="padding-top:20px">
    <?php
    if (isset($nb_exp_completed) && $nb_exp_completed > 0) {
        if (isset($_SESSION['username'])) {
            echo 'Benvenuto <b><a href="#" id="userProfile">' . htmlspecialchars($_SESSION['username']) . ' Hai sbloccato una nuova feature! cliccami!</a></b>!';
        } else {
            echo "ERROR: no username field found.";
        }
    } else {
        if (isset($_SESSION['username'])) {
            echo 'Benvenuto <b>' . htmlspecialchars($_SESSION['username']) . '</b>!';
        } else {
            echo "ERROR: no username field found.";
        }
    }


    ?></p>
<p>Questa è la tua pagina personale per navigare attraverso i vari ascolti. Ogni ascolto sarà accessibile solo dopo aver completato quelli precedenti.</p>

<?php if (!$preliminary_done) {echo '
<p>Per iniziare, ti chiediamo di compilare un breve questionario che ci permetterà di raccogliere informazioni riguardanti la tua personalità, dati socio-demografici e il tuo rapporto con la musica.
    I dati sono raccolti e processati in completa anonimità, in conformità con le normative vigenti (D. Lgs 196/2003 e UE GDPR 679/2016) sulla protezione dei dati, garantendo la tua privacy.</p>
';} ?>

<p>Puoi ascoltare quanti esperimenti vuoi in sessioni di ascolto diverse nell'arco di più giorni rieseguendo il login con le credenziali registrate. I dati e i progressi delle sessioni rimarranno salvati.
    Ti chiediamo di completare ciascun esperimento di ascolto in un'unica sessione. Ciascuna sessione rimarrà valida per 1 ora e mezza
    durante la quale sarà possibile recuperare i progressi della sessione di ascolto, qualora si dovessero presentare problemi con la connessione o il caricamento di alcune tracce audio.</p>

<p>Ciascun esperimento d'ascolto corrisponde ad una sinfonia di musica classica. Ciascuna sinfonia è divisa in quattro movimenti intervallati da una breve pausa.
    Durante l'ascolto ti chiediamo di svolgere un semplice compito che non inficierà l'ascolto per garantire un'esperienza coinvolgente.
    Ciascuna sinfonia dura fra i 30 e 45 minuti. Il titolo della sinfonia ascoltata sarà mostrato in questa pagina una volta terminato ciascun ascolto.</p>

<p>Grazie per il tuo contributo. Esplora, partecipa e scopri di più sulla musica e sul suo impatto emotivo!
</p>
<p>Per qualsiasi informazione o problema scrivi a: matteo.lionello [chiocciola] imtlucca [punto] it</p>

<ul style="line-height: 2;">
    <li>
        <?php
        if (!$preliminary_done) {
            echo '<a href="#" id="exp0"><b>Demographics and Music Proficiency Questionnaire<b></a>';
        } else {
            echo '<b style="color:grey">Demographics and Music Proficiency Questionnaire: Completed!</b>';
        }
        ?>
    </li>

    <?php
    $link_enabled = $preliminary_done;
    for ($i = 0; $i < $nb_total_exp; $i++) {
        if ($i < $nb_exp_completed) {
            echo '<li style="color:grey"><b> Listening experiment ' . ($i + 1) . ' completed!</b> You listened to ' . $listened_to[$i] . '</li>';
        } else {
            echo '<li>' . ($link_enabled ? '<a href="#" class="exp_link"><b>Experiment ' . ($i + 1) . ' </b></a>' : 'Listening experiment ' . ($i + 1) . ' <i style="font-size:14px">[LOCKED]</i>') . '</li>';
            $link_enabled = false;
        }
    }
    ?>
</ul>

<form id="logoutForm">
    <button type="submit">Log Out</button>
</form>

<script>
    $(document).off('click', '#userProfile').on('click', '#userProfile', function (e) {
        e.preventDefault();

        $.ajax({
            url: 'user_statistics.php', // This is the PHP file we will create
            method: 'GET',
            dataType: 'html',
            success: function (response) {
                $('#contentContainer').html(response); // Load the content into the main container
            },
            error: function () {
                alert('Failed to load user statistics.');
            }
        });
    });

    $(document).off('click', '#exp0').on('click', '#exp0', function (e) {
        e.preventDefault();
        load_questionnaires();
    });

    $(document).off('click', '.exp_link').on('click', '.exp_link', function (e) {
        e.preventDefault();
        let questions_dict; let questions_container; let debug;
        let audioPlayerexample; let startexampleButton; let stopexampleButton; let startexp;
        let sub_question_dict1; let sub_question_dict2;
        loadExperiment();
    });

    function loadExperiment() {
        $.ajax({
            url: 'build_experiment.php',
            method: 'POST',
            dataType: 'json',
            success: function (response) {
                $('#contentContainer').html(response.content);
            },
            error: function () {
                alert('dashboar. loadExperiment. Failed to load the experiment.');
            }
        });
    }

    function load_questionnaires() {
        $.ajax({
            url: 'preliminary_questionnaires.php',
            method: 'POST',
            dataType: 'json',
            success: function (response) {
                if (response.success) {
                    $('#contentContainer').html(response.content);
                } else {
                    alert('Failed to load the questionnaires. Try again.');
                }
            },
            error: function () {
                alert('Failed to load the questionnaires.');
            }
        });
    }
<?php
if (isset($_SESSION["debug"]) && $_SESSION["debug"]) {
echo '
    $(document).ready(function() {
        $("#debug").load("debug.php");
    })
';
} ?>
</script>

<?php
$content = ob_get_clean();
echo json_encode(['success' => true, 'content' => $content]);
?>
