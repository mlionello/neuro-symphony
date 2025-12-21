<?php

//function isMobile() {
//    return preg_match('/(android|iphone|ipad|ipod|mobile|blackberry|iemobile|opera mini|windows phone|webos|palm|symbian)/i', $_SERVER['HTTP_USER_AGENT']);
//}

//if (isMobile()) {
//    echo "<p style='text-align: center; font-size: 2.4em; color: red;'>This site is not supported on mobile devices. Please visit on a desktop for the best experience.</p>";
//    exit; // Stops further page rendering if on mobile
//}

session_start();

if (isset($_GET['debug'])) {
    $_SESSION['debug'] = filter_var($_GET['debug'], FILTER_VALIDATE_BOOLEAN);
}

if (!isset($_SESSION['debug'])) {
    $_SESSION['debug'] = filter_var(0, FILTER_VALIDATE_BOOLEAN);
}

//if (!$_SESSION['debug']) {
//echo "sito in aggiornamento: per favore ritenta dopo le 11:30 - 10 febbraio 10:00";
//exit;
//}

$_SESSION['current_date'] = date('Y-m-d H:i:s');


if (isset($_GET['lang'])) {
    // Set the session variable to the value of the 'lang' parameter
    $_SESSION['lang'] = $_GET['lang'];
}


// Assign to the user the descriptors categories
if (!isset($_SESSION['lang'])) {
    $_SESSION['lang'] = "ita"; // Default language
}

// Check if user is logged in
$isLoggedIn = isset($_SESSION['username']) && !empty($_SESSION['username']);

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neuro Symphony</title>
    <script src="./js/jquery-3.7.1.min.js"></script>
    <link rel="stylesheet" type="text/css" href="css/styles.css">
    <script>


            // Function to Hide Buttons
            function hideButtons() {
                $('#welcome').hide();
            }

            // Bind Logout Form Submission
            function bindLogoutForm() {
                $('#logoutForm').on('submit', function (e) {
                    e.preventDefault();

                    $.ajax({
                        url: 'logout.php',
                        type: 'GET',
                        dataType: 'json',
                        success: function (response) {
                            if (response.success) {
                                let countdown = 3; // Start with 3 seconds

                                // Display the initial message
                                $('#contentContainer').html(`<p>You have successfully logged out. The page will reload in <span id="countdown">${countdown}</span> seconds...</p>`);

                                // Update the countdown every second
                                let interval = setInterval(function () {
                                    countdown--;
                                    $('#countdown').text(countdown); // Update the countdown number in the message

                                    if (countdown <= 0) {
                                        clearInterval(interval); // Stop the interval
                                        location.reload(); // Reload the page
                                    }
                                }, 1000); // Update every second
                            } else {
                                alert('Logout failed. Please try again.');
                            }
                        },
                        error: function () {
                            alert('Failed to log out. Please try again.');
                        }
                    });
                });
            }

            // Function to Load Dashboard
            function loadDashboard() {
                $.ajax({
                    url: 'dashboard.php',
                    method: 'POST',
                    dataType: 'json',
                    success: function (response) {
                        if (response.success) {
                            $('#contentContainer').html(response.content);
                            bindLogoutForm();
                        }
                    }
                });
            }

        $(document).ready(function () {
            <?php if ($isLoggedIn): ?>
                // User is logged in, load the dashboard directly
                loadDashboard();
                hideButtons();
            <?php endif; ?>

            // Load Login Form
            $('#btnLogin').click(function () {
                $.ajax({
                    url: 'login.php',
                    method: 'POST',
                    dataType: 'json',
                    success: function (response) {
                        if (response.success) {
                            $('#subconnectcontent').html(response.content);
                        }
                    }
                });
            });

            // Load Signup Form
            $('#btnSignup').click(function () {
                $.ajax({
                    url: 'signup.php',
                    method: 'POST',
                    dataType: 'json',
                    success: function (response) {
                        if (response.success) {
                            $('#subconnectcontent').html(response.content);
                        }
                    }
                });
            });



        });
    </script>
</head>
<body>
    <div id="contentContainer" class="container_init">
        <?php if ($isLoggedIn): ?>
            <p>Loading dashboard...</p>
        <?php else: ?>
                <h1>Neuro Symphony - A platform for music and neuroscience experiments</h1>
        <div id="subconnectcontent" style="padding-top:20px">
            <div id="welcome-message">
        <p>Benvenuto/a!</p>
            <p>Ti diamo il benvenuto nel portale degli esperimenti di ascolto musicale, promosso dall'unità di ricerca Social and Affective Neuroscience (SANe)
            presso IMT Scuola di Alti Studi di Lucca. Per iniziare, registrati e connettiti alla piattaforma. I dati sono raccolti e processati in completa anonimità, in conformità con le
            normative vigenti (D. Lgs 196/2003 e UE GDPR 679/2016) sulla protezione dei dati garantendo la tua privacy.</p>
	   <p>Per informazioni o per segnalare un problema puoi scrivere una email indirizzata a: <span style="white-space: nowrap"><i>matteo.lionello [chiocciola] imtlucca [punto] it</i></span></p>
            </div>
        <div id="login-buttons">
        <button id="btnLogin">Login</button>
        <button id="btnSignup">Sign Up</button>
        </div>
        <?php endif; ?>
    </div>

    <pre id='debug'>
    </pre>

<?php
if (isset($_SESSION['debug']) && $_SESSION['debug']) {
    echo '
        <script>
        $(document).ready(function() {
        $("#debug").load("debug.php");
        })
        </script>
    ';
} ?>
</body>
</html>
