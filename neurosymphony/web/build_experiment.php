<?php
function isMobile() {
    return preg_match('/(android|iphone|ipad|ipod|mobile|blackberry|iemobile|opera mini|windows phone|webos|palm|symbian)/i', $_SERVER['HTTP_USER_AGENT']);
}

if (isMobile()) {
    //echo json_encode(['success' => true, 'content' => "This site is not supported on mobile devices. Please visit on a desktop for the best experience."]);
    echo json_encode(['success' => true, 'content' => "<p style='text-align: center; font-size: 16px; color: red;'>L'esperimento non e' disponibile da dispositivi mobile. Per favore accedi tramite computer desktop o portatile.</p>"]);
    exit; // Stops further page rendering if on mobile
}

session_start();

include __DIR__ . '/php/assign_expid_cond.php';
require __DIR__ . '/php/load_csv.php';

$user_id = $_SESSION['user_id'];
$file_path = $_SESSION['user_file_path'];
$overall_data_path = $_SESSION['overall_consts'];

// Load the JSON file content
$user_data = json_decode(file_get_contents($file_path), true);
$all_data = json_decode(file_get_contents($overall_data_path), true);

$completed_exp = $user_data["completed_exp_id"];

$new_log_row = true;
$reset_time_individual_session = 6300;
$reset_time_started_sessions = 6300;
if (!isset($user_data['experiment_started_time']) || empty($user_data['experiment_started_time']) || time() - $user_data['experiment_started_time'] > $reset_time_individual_session) {
    list($_SESSION['experiment_id'], $_SESSION['assigned_condition']) = get_experiment_id($completed_exp, $_SESSION['experiment_log'], $reset_time_started_sessions);
    $_SESSION['step'] = "welcome";
} else {
    $started_exp_id = $user_data['experiment_id'];
    $_SESSION['experiment_id'] = $started_exp_id;
    $_SESSION['assigned_condition'] = $user_data[$started_exp_id]['session_data']["assigned_condition"];
    $_SESSION['description_indices'] = $user_data[$started_exp_id]['session_data']["description_indices"];
    $_SESSION['step'] = $user_data[$started_exp_id]["step"];
    $_SESSION['track_index'] = isset($user_data[$started_exp_id]["track_index"]) ? $user_data[$started_exp_id]["track_index"] : 0;
    $new_log_row = false;
}

// if (($handle = fopen($_SESSION['exp_conditions'], "r")) !== FALSE) {
if (($handle = fopen($all_data[$_SESSION['experiment_id']]['exp_conditions'], "r")) !== FALSE) {
    $currentIndex = 0;
    $_SESSION['cond_per_session'] = [];

    // Loop through each row in the CSV file
    while (($row = fgetcsv($handle, 0, ',', '"', '\\')) !== FALSE) {
        if ($currentIndex == $_SESSION['assigned_condition']) {
            // Convert each item in the row to an integer
            $_SESSION['cond_per_session'] = array_map('intval', $row);
            break; // We found the row we need, exit the loop
        }
        $currentIndex++;
    }

    fclose($handle); // Close the file

} else {
    echo "Error: Could not open CSV file.";
}

if (!isset($_SESSION['description_indices']) ||  $_SESSION['debug']) {
    // Offset defines the starting index for each movement's set of samples
    $num_samples = $all_data[$_SESSION['experiment_id']]['number_descriptions_per_mvt'];
    if ( $_SESSION['debug'] ) {
        $num_samples = $all_data['number_descriptions_per_mvt_debug'];
    }
    $offset = [0, $num_samples, 2*$num_samples, 3*$num_samples];
    $_SESSION['description_indices'] = [];
    $_SESSION['description_indices'][] = $offset[$_SESSION['cond_per_session'][0] - 1];     // TT: Exact offset
    $_SESSION['description_indices'][] = $offset[$_SESSION['cond_per_session'][1] -1 ] + 1; // TF: offset + 1
    $a = rand(2, $num_samples - 1); if ( $a % 2 != 0 ) { $a = $a - 1;};
    $_SESSION['description_indices'][] = $offset[$_SESSION['cond_per_session'][2] - 1] + $a;  // FT: Random index even
    $a = rand(3, $num_samples - 1); if ( $a % 2 == 0 ) { $a = $a - 1;};
    $_SESSION['description_indices'][] = $offset[$_SESSION['cond_per_session'][3] - 1] + $a;  // FF: Random index odd

    sort($_SESSION['description_indices']);
}

if (isset($_SESSION['lang']) && $_SESSION['lang'] == "ita") {
    $_SESSION['labels'] = array_map( function($v){return str_getcsv($v, ",", "\"", "\\");}, file($all_data['labels_path']));
    $description_file = $all_data[$_SESSION['experiment_id']]['description_path'];
} else {
    $_SESSION['labels'] = array_map( function($v){return str_getcsv($v, ",", "\"", "\\");}, file($all_data['labels_path_eng']));
    $description_file = $all_data[$_SESSION['experiment_id']]['description_path_eng'];
}

$_SESSION['audioPaths'] = loadCSV($all_data[$_SESSION['experiment_id']]['audio_path_file']);
if ( $_SESSION['debug'] ) {
    $_SESSION['audioPaths'] = loadCSV($all_data['audio_path_debug']);
    $description_file = $all_data['description_debug'];
}
$_SESSION['descriptions'] = loadCSV($description_file, $_SESSION['description_indices']);

if ($new_log_row) {
    $log_row = [
        $user_id,                       // User ID
        time(),                         // Current timestamp
        $_SESSION['experiment_id'],     // Experiment ID that started
        '',                             // Experiment ID that finished (empty for now)
        $_SESSION['assigned_condition'] // Assigned condition
    ];

    try { // TODO: check what happens when the same user resume an interrupted session
        $file = fopen($_SESSION['experiment_log'], 'a'); // Open log.csv in append mode
        if ($file !== false) {
            fputcsv($file, $log_row, ',', '"', '\\'); // Add the row to the CSV file
            fclose($file); // Close the file
        } else {
            throw new Exception("Unable to open log file.");
        }
    } catch (Exception $e) {
        error_log("Error logging to CSV: " . $e->getMessage());
    }
}

ob_start();
?>
<div id="lang" style="display:none;"><?php echo $_SESSION['lang']; ?></div>
<div id="content-section"></div>

<script>
var element = document.getElementById("contentContainer");
element.classList.remove("container_init");
$(document).ready(function() {
    function loadNextSection(current_section) {
        $.ajax({
            url: 'php/load_section.php',
            type: 'POST',
            data: {section: current_section},
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    $('#content-section').html(response.content);
                    window.scrollTo({
                        top: 0,
                    });
                } else {
                    alert(response.message || 'Failed to load the next section..');
                }
            },
            error: function() {
                alert('Failed to load the next section!' + current_section);
            }
        });
    }

    $(document).off('submit', 'form.submit-and-proceed').on('submit', 'form.submit-and-proceed', function (event) {
        event.preventDefault();

        let formData = $(this).serializeArray();
        let currentSection = formData.find(item => item.name === 'current_section').value;

        formData.push({ name: 'exp_id', value: "<?php echo $_SESSION['experiment_id']; ?>" });
        formData.push({ name: 'descriptions_class', value: "<?php echo $_SESSION['assigned_condition']; ?>" });

        $.ajax({
            url: 'php/save_response.php',
            type: 'POST',
            data: formData,
            success: function() {
               console.log('Data saved successfully.');
               loadNextSection(currentSection);
            },
            error: function() {
                console.log('Error saving data.');
            }
        });
    });

    let restore_section = "<?php echo $_SESSION['step']; ?>";
    if (restore_section==='welcome' ) {
        $.ajax({
            url: 'php/restore_section.php',
            type: 'POST',
            data: {section: restore_section},
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    $('#content-section').html(response.content);
                } else {
                    alert(response.message || 'Failed to restore the section..');
                }
            },
            error: function() {
                alert('Failed to restore the section...');
            }
        });
    } else {
        loadNextSection(restore_section);
    }
    <?php
    if (isset($_SESSION["debug"]) && $_SESSION["debug"]) {
    echo '
         $("#debug").load("debug.php");
    ';
    } ?>
});

</script>
<?php
$content = ob_get_clean();
echo json_encode(['success' => true, 'content' => $content]);
?>
