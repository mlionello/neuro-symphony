<?php
header('Content-Type: application/json');

ob_start(); // Start output buffering
?>
<h2>Sign Up</h2>
<form id="signupForm">
    <p> Please choose a username and password. You may also provide an email address for potential future password recovery.
        Both the username and password are securely hashed, and the email address is encrypted via
        AES-256-CBC algorithm - with a user-specific key that cannot be retrieved by anyone, including our staff. These sensitive data elements cannot be accessed by our staff or anyone else.
        If needed, a password recovery request will be sent automatically to the registered email address.
        All data is stored and processed in a fully anonymized manner to ensure your privacy.
    </p>
    <label for="signupUsername">Username*:</label><br>
    <input type="text" id="signupUsername" class="accesscredentials-input" name="username" required  style="width:300px">
    <br><br>
    <label for="signupEmail">Email address:</label><br>
    <input type="text" class="accesscredentials-input" id="signupEmail" name="email" style="width:400px">
    <br><br>
    <label for="signupPassword">Password*:</label>
    <input type="password" class="accesscredentials-input" id="signupPassword" name="password" required>
    <br><br>
    <button type="submit">Submit</button>
</form>
<div id="signupMessage"></div>
<button class="HomeButton">Back</button>

<script>
    // Bind Signup Form Submission
    $('#signupForm').on('submit', function (e) {
        e.preventDefault();
        $.ajax({
            url: 'process_signup.php',
            type: 'POST',
            data: $(this).serialize(),
            dataType: 'JSON',
            success: function (response) {
                if (response.success) {
                    let countdown = 5;
                    $('#contentContainer').html(`<p style='color:green'>${response.message}</p><p>The page will reload in <span id="countdown">${countdown}</span> seconds...</p>`);
                    let interval = setInterval(function () {
                        countdown--;
                        $('#countdown').text(countdown);
                        if (countdown <= 0) {
                            clearInterval(interval);
                            location.reload();
                        }
                    }, 1000);
                } else {
                    $('#signupMessage').html(`<p style='color:red'>${response.message}</p>`);
                }
            },
            error: function() {
                $('#signupMessage').html(`<p style='color:red'>Internal Error.</p>`);
            }
        });
    });

    $('.HomeButton').click(function() {
        location.reload(); // Reload the page
    });
</script>

<?php
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>
