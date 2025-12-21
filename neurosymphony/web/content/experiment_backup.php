<?php
// Function to load CSV data
function loadCSV($filename) {
    $rows = array_map('str_getcsv', file($filename));
    $header = array_shift($rows);
    $csv = [];

    foreach ($rows as $row) {
        if (count($header) !== count($row)) {
            continue;  // Skip the malformed row
        }
	$data = array_combine($header, $row);
        $csv[] = $data;
    }

    return $csv;
}

$audioPaths = loadCSV('audio_paths.csv');
$descriptions = loadCSV('description.csv');

// Combine audio paths and descriptions based on track number
$tracks = [];
foreach ($audioPaths as $path) {
    foreach ($descriptions as $desc) {
        if ($path['track_number'] == $desc['track_number']) {
            $tracks[] = [
                'file' => $path['path'],
                'description' => $desc['description']
            ];
            break;
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Music Experiment</title>
    <link rel="stylesheet" type="text/css" href="styles.css">
    <script>
        let sliderData = [];
        let startTime;
        let intervalId;
        let currentTrack = 0;
        let tracks = <?php echo json_encode($tracks); ?>; // Load tracks from PHP
        function loadTrack(trackIndex) {
            if (trackIndex < tracks.length) {
                let track = tracks[trackIndex];
                document.getElementById('trackTitle').innerText = `Track ${trackIndex + 1}`;
                document.getElementById('trackDescription').innerText = track.description;
                let startbutton = document.getElementById('startsong');
                startbutton.display = "block";
                let audioPlayer = document.getElementById('audioPlayer');
                audioPlayer.src = track.file;

                // Update track counter
                document.getElementById('trackCounter').innerText = `Track ${trackIndex + 1}/${tracks.length}`;

                // Show description overlay
                document.getElementById('descriptionOverlay').style.display = 'block';

                sliderData = []; // Reset slider data for the new track
            } else {
                //window.location.href = 'post_experiment.php'; // Redirect to post-experiment questionnaire if no more tracks
            }
        }

        function startExperiment() {
            startTime = Date.now();
            let audio = document.getElementById('audioPlayer');
            let startbutton = document.getElementById('startsong');
            startbutton.display = "none";
            audio.play().catch(error => {
                console.error("Error playing audio:", error);
            });

            // Hide description overlay
            document.getElementById('descriptionOverlay').style.display = 'none';

            // Store the initial "101" value at the start
            let sliders = document.querySelectorAll('.slider');
            let initialValues = Array.from(sliders).map(slider => 101);
            initialValues.unshift(0); // Timestamp 0
            sliderData.push(initialValues);

            intervalId = setInterval(() => {
                let timestamp = Date.now() - startTime;
                let values = Array.from(sliders).map(slider => slider.value);
                values.unshift(timestamp);
                sliderData.push(values);
            }, 100); // 10 times per second

            audio.onended = function() {
                clearInterval(intervalId);
                saveData();
                currentTrack++;
                //loadTrack(currentTrack); // Load the next track
            };
        }

        function saveData() {
            let xhr = new XMLHttpRequest();
            xhr.open("POST", "save_experiment_data.php", true);
            xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xhr.send(JSON.stringify(sliderData));
        }

        window.onload = function() {
            loadTrack(currentTrack); // Manually load the first track when the page loads
        };
    </script>
</head>
<body>
    <div id="descriptionOverlay">
        <h1 id="trackTitle">Track 1</h1>
        <p id="trackDescription">Description of the first track.</p>
        <button onclick="document.getElementById('descriptionOverlay').style.display='none'">I have read it</button>
    </div>

    <div class="experiment-container">
        <div class="sliders-container">
        <button id="startsong" onclick="startExperiment()">Start Song</button><br>
            <label for="slider1">Slider 1:</label>
            <input type="range" class="slider" id="slider1" min="0" max="100" value="50"><br><br>

            <label for="slider2">Slider 2:</label>
            <input type="range" class="slider" id="slider2" min="0" max="100" value="50"><br><br>

            <label for="slider3">Slider 3:</label>
            <input type="range" class="slider" id="slider3" min="0" max="100" value="50"><br><br>

            <label for="slider4">Slider 4:</label>
            <input type="range" class="slider" id="slider4" min="0" max="100" value="50"><br><br>
        </div>

        <audio id="audioPlayer" src=""></audio>
        <button onclick="saveData()" style="display:none">tmp save</button>

        <div id="trackCounter" class="track-counter">Track 1/<?php echo count($tracks); ?></div>
    </div>
</body>
</html>
