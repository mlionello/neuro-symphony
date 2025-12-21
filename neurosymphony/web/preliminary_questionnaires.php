<?php
session_start();

$userId = $_SESSION['user_id'];
$fileName = $_SESSION['user_file_path'];

$directory = dirname($fileName);

// Check if the directory exists, and create it if it doesn't
if (!is_dir($directory)) {
    mkdir($directory, 0777, true); // Creates the directory with recursive permissions
}

// Initialize an array to hold the response data
$responses = [];

// Check if the JSON file already exists
if (file_exists($fileName)) {
    // Read the existing data
    $existingData = file_get_contents($fileName);
    $responses = json_decode($existingData, true) ?: []; // Decode or use an empty array
}

if (isset($responses['demographics_and_GMSI']['step'])) {
$_SESSION['step'] = $responses['demographics_and_GMSI']['step'];
}

if (!isset($_SESSION['step'])) {
    $_SESSION['step'] = "terms";
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
            url: 'php/load_pages_questionnaires.php',
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
                    alert(response.message || 'Failed to load the next section.');
                }
            },
            error: function() {
                alert('Failed to load the next section.');
            }
        });
    }

    $(document).off('submit', 'form.submit-and-proceed').on('submit', 'form.submit-and-proceed', function (event) {
        event.preventDefault();

        let formData = $(this).serializeArray();
        let currentSection = formData.find(item => item.name === 'current_section').value;

        if (currentSection === 'demographics') {
            let psychiatricDiagnosis = formData.find(item => item.name === 'psychiatric_diagnosis')?.value.toLowerCase();
            let psychiatricTreatment = formData.find(item => item.name === 'psychiatric_treatment')?.value.toLowerCase();
            let native_lanugage = formData.find(item => item.name === 'mother_tongue')?.value.toLowerCase();

            if (psychiatricDiagnosis === 'yes' || psychiatricTreatment === 'yes' || native_lanugage !== 'it') {
                $.ajax({
                    url: 'php/restore_section.php',
                    type: 'POST',
                    data: {section: 'cannotproceed'},
                    success: function(response) {
                        $('#content-section').html(response.content);
                    },
                    error: function() {
                        alert('Failed to load the cannot proceed section.');
                    }
                });
                return;
            }
        }

        formData.push({ name: 'exp_id', value: 'demographics_and_GMSI' });

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
    if (restore_section==='terms' ) {
        $.ajax({
            url: 'php/restore_section.php',
            type: 'POST',
            data: {section: restore_section},
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    $('#content-section').html(response.content);
                } else {
                    alert(response.message || 'Failed to restore the section.');
                }
            },
            error: function() {
                alert('Failed to restore the section.');
            }
        });
    } else {
        loadNextSection(restore_section);
    }

});
</script>
<?php
$content = ob_get_clean();
echo json_encode(['success' => true, 'content' => $content]);
?>
