<?php
session_start();

// Ensure the user is logged in
if (!isset($_SESSION['user_id']) || !isset($_SESSION['username'])) {
    die("Access denied. Please log in.");
}

$userid = $_SESSION['user_id'];
$username = $_SESSION['username'];
$log_file = $_SESSION['experiment_log'];

$user_data = json_decode(file_get_contents($_SESSION['user_file_path']), true);
$all_data = json_decode(file_get_contents($_SESSION['overall_consts']), true);


$expid = array_unique($user_data['completed_exp_id']) ?? [];
$nb_exp_completed = count($expid);
$exp_id_questionnaires = 'demographics_and_GMSI';
$preliminary_done = $user_data[$exp_id_questionnaires]['status'] === 'done';

$handle = fopen($log_file, "r");
$user_experiments = [];
$user_completion_counts = [];

// Read all users' data to compare progress
while (($data = fgetcsv($handle, 0, ',', '"', '\\')) !== false) {
    list($log_userid, $time, $exp_started, $exp_ended, $param) = $data;

    // Track user progress
    if (!isset($user_completion_counts[$log_userid])) {
        $user_completion_counts[$log_userid] = 0;
    }

    // Count completed experiments per user
    if (!empty($exp_ended)) {
        $user_completion_counts[$log_userid]++;
    }

    // Store the logged-in user's experiment details
    if ($log_userid === $userid) {
        $user_experiments[] = [
            'time' => $time,
            'exp_started' => $exp_started,
            'exp_ended' => $exp_ended,
        ];
    }
}
fclose($handle);

// Counting total number of users registered
$users_file = 'users.csv'; // Path to your users.csv file
$users_count = 0;
if (file_exists($users_file)) {
    $users_handle = fopen($users_file, "r");
    while (!feof($users_handle)) {
        fgets($users_handle);
        $users_count++;
    }
    fclose($users_handle);
}


$exp_data = [];
foreach ($expid as $exp) {
    $start_times = [];

    foreach ($user_experiments as $ue) {
        if ($ue['exp_started'] == $exp) {
            $start_times[] = $ue['time'];
        }
        if ($ue['exp_ended'] == $exp) {
            $end_time = $ue['time'];
        }
    }

    if (!empty($end_time) && !empty($start_times)) {
        $duration = $end_time - max($start_times); // Calculate the shortest duration for the experiment
        $exp_data[] = [
            'start_time' => date("Y-m-d H:i:s", max($start_times)),
            'duration' => date("i:s", $duration),
            'title' => $all_data[$exp]['title']
        ];
    }
}

function findPeakFrequency(array $start_times) {
    if (empty($start_times)) return "Undefined"; // Return if no data available

    sort($start_times); // Ensure the times are in chronological order
    $peak_frequency = 0;
    $window_start = strtotime($start_times[0]);
    $window_end = $window_start + (10 * 24 * 60 * 60); // 10 days in seconds

    $current_count = 0;
    foreach ($start_times as $time) {
        $timestamp = strtotime($time);
        if ($timestamp <= $window_end) {
            $current_count++; // Increment count within the current window
        } else {
            $peak_frequency = max($peak_frequency, $current_count);
            // Move the window
            while ($timestamp > $window_end) {
                $window_start = $window_end;
                $window_end = $window_start + (10 * 24 * 60 * 60);
                $current_count = ($timestamp >= $window_start && $timestamp <= $window_end) ? 1 : 0;
            }
        }
    }
    $peak_frequency = max($peak_frequency, $current_count); // Check last window

    return $peak_frequency; // Return the highest frequency found
}

function categorizeUserByPeakFrequency($peak_frequency) {
    if ($peak_frequency < 1) return "Patata da Divano: chi va piano va sano e lontano... ma gli sperimentatori non raccolgono dati! <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F422.svg\"/>";
    if ($peak_frequency < 2) return "Guerriero del Weekend: prova a fare qualche ascolto in più durante la settimana! <img class=\"emoji\"  src=\"fonts/openmoji-svg-color/1F5E1.svg\"/>
        <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F6E1.svg\"/>";
    if ($peak_frequency < 3) return "Appassionato: Bel vigore, continua così! <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F4AA.svg\"/>
     <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F31F.svg\"/>";
    if ($peak_frequency < 4) return "Inarrestabile: Wow, sei una fiamma!! <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F525.svg\"/>
      <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F525.svg\"/>";
    if ($peak_frequency < 5) return "Topo da Laboratorio: Non ti fermi mai, eh?<img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F400.svg\"/>
      <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F52C.svg\"/>";
    if ($peak_frequency < 7) return "Scienziato Razzo: Sfrecci attraverso gli esperimenti!!! <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F469-200D-1F52C.svg\"/>
     <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F680.svg\"/>" ;
    return "Signore del Tempo: Pieghi il tempo per fare più esperimenti!!!!!!! <img class=\"emoji\" src=\"fonts/openmoji-svg-color/23F3.svg\"/>
     <img class=\"emoji\" src=\"fonts/openmoji-svg-color/2728.svg\"/>
      <img class=\"emoji\" src=\"fonts/openmoji-svg-color/1F9D9.svg\"/>";
}


// Extract start times from exp_data for frequency analysis
$all_start_times = array_map(function($data) {
    return $data['start_time'];
}, $exp_data);

if (count($all_start_times)>1) {
    // Find peak frequency using all extracted start times
    $peak_frequency = findPeakFrequency($all_start_times);
    // Categorize user by this peak frequency
    $user_frequency_category = categorizeUserByPeakFrequency($peak_frequency);
    } else {
        $user_frequency_category = "N\A - Fai un\'altro ascolto per sbloccare questa feature!";
    }


// Sort users by completion count (highest first)
arsort($user_completion_counts);
$completion_values = array_values($user_completion_counts);

// Calculate user's percentile ranking
$user_rank = array_search($nb_exp_completed, $completion_values) + 1; // Rank starts at 1
$total_users = count($completion_values);
$percentile = round(100 - (($user_rank / $total_users) * 100), 2);

// Define levels based on completed experiments
$levels = [
    0  => "Turista Uditivo: Benvenuto nel mondo del suono!",
    1  => "Esploratore Sonoro: hai appena iniziato a scoprire!",
    3  => "Cacciatore di Melodie: Sei sulla traccia giusta!",
    5  => "Architetto Musicale: Costruisci ponti sonori!",
    7  => "Mago delle Armonie: Stregone delle scale musicali!",
    8  => "Divinità del Ritmo: Dirigi il mondo a tuo piacimento!"
];

$user_level = "Ascoltatore Novizio";
foreach ($levels as $threshold => $level) {
    if ($nb_exp_completed >= $threshold) {
        $user_level = $level;
    }
}
?>

<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="css/progress.css" rel="stylesheet" />
    <title>Statistiche Personali</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .container { max-width: 900px; margin: auto; }
        h2 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f4f4f4; }
        .emoji {width:30px; width:30px}

        #level {
            position: relative;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
<?php
$hour = date('H');
if ($hour < 12) {
    $greeting = "Buongiorno";
} elseif ($hour < 18) {
    $greeting = "Buon pomeriggio";
} else {
    $greeting = "Buona sera";
}
?>
        <h2><?php echo $greeting . " " . $username . "!"; ?> Ecco la tua scheda di progresso!</h2>

        <div class="progress-bar-wrapper"></div>

        <script src="js/progress-bar.js"></script>
    <script>
        let list_steps = ['Questionario', '1imo Ascolto', '2ndo Ascolto', '3erzo Ascolto',
                          '4uarto Ascolto', '5uinto Ascolto', '6esto Ascolto', 'Penultimo Ascolto',
                          'Ultimo Ascolto'];

        let current_step = "";

        <?php
        if ($preliminary_done) {
            echo 'current_step = "Questionario";';
        }

        if (count($expid) > 0) {
            echo 'current_step = list_steps[' . (count($expid)) . '];';
        }
        ?>

        ProgressBar.singleStepAnimation = 200;
        ProgressBar.init(list_steps, current_step, 'progress-bar-wrapper');
    </script>


        <p><strong>Percentile Ranking:</strong>
        <?php
        if ($nb_exp_completed>0){
            if ($percentile > 98) {
                echo "SUPER!!!! ";
            } elseif ($percentile > 90) {
                echo "WOW! ";
            } elseif ($percentile > 80) {
                echo "Congratulazioni!! ";
            }}
        ?>
        Il tuo punteggio e' piu alto del <strong><?php echo $percentile; ?>%</strong> degli ascoltatori! (totale partecipanti <strong><?php echo $users_count; ?></strong>)<br>
        <?php
            if ($percentile > 98) {
                echo "Sei sulla cima della classifica!!!!</p>";
            } elseif ($percentile > 90) {
                echo "Ottimo lavoro!</p>";
            } elseif ($percentile > 80) {
                echo "Complimenti per il tuo punteggio!</p>";
            } else {
                echo "Continua così!</p>";
            }
        ?>
        <p id="level">Livello attuale: <strong id="rpgtrigger" onclick="loadRPGResources()"><?php echo $user_level; ?></strong></p>
        <p>Il tuo livello di frequenza degli esperimenti:  <strong><?php echo $user_frequency_category; ?></strong></p>
        <script>
            function loadRPGResources() {

            // Load CSS
            var link = document.createElement('link');
            link.rel = 'stylesheet';
            link.type = 'text/css';
            link.href = 'css/rpg.css';
            document.head.appendChild(link);

            // Load JS
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = 'js/rpg.js';
            document.body.appendChild(script);
            }

        </script>
        <br><br>
        <h3>Storico Esperimenti</h3>
        <table>
            <tr>
                <th>Data</th>
                <th>Ascolto</th>
                <th>Durata</th>
            </tr>
            <?php foreach ($exp_data as $exp): ?>
            <tr>
                <td><?php echo $exp['start_time']; ?></td>
                <td><?php echo $exp['title'] ?? '-'; ?></td>
                <td><?php echo $exp['duration'] ?: '-'; ?></td>
            </tr>
            <?php endforeach; ?>
        </table>
    </div>
<button class="HomeButton">Indietro</button>
<script>
        $('.HomeButton').click(function() {
        location.reload(); // Reload the page
    });
</script>
</body>
</html>
