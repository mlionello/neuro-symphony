<?php
header('Content-Type: application/json');

ob_start(); // Start output buffering
?>
<h2>Login</h2>
<form id="loginForm">
    <label for="loginUsername">Username:</label><br>
    <input type="text" class="accesscredentials-input" id="loginUsername" name="username" required style="width:300px">
    <br><br>
    <label for="loginPassword">Password:</label>
    <input type="password" class="accesscredentials-input" id="loginPassword" name="password" required>
    <br><br><br>
    <button type="submit">Submit</button>
</form>
<div id="loginMessage"></div>
<button class="HomeButton">Back</button>
<button id="requestPassword" style="display:none;">Request Password Reset</button>

<script>
    // Bind Login Form Submission
    $('#loginForm').on('submit', function (e) {
        e.preventDefault();
        $.ajax({
            url: 'process_login.php',
            type: 'POST',
            data: $(this).serialize(),
            dataType: 'JSON',
            success: function (response) {
                if (response.success) {
                    loadDashboard(); // Call the dashboard loading function
                    hideButtons();   // Hide login and signup buttons
                } else {
                    $('#loginMessage').html(`<p style="color: red;">${response.message}</p>`);
                    $('#requestPassword').show(); // Show the Request Password Reset button if login fails
                }
            },
            error: function () {
                $('#loginMessage').html('<p style="color: red;">An error occurred. Please try again.</p>');
                $('#requestPassword').show(); // Show the Request Password Reset button on AJAX error too
            }
        });
    });

    // Bind the Request Password Reset button
    $('#requestPassword').click(function() {
        var username = $('#loginUsername').val(); // Get the username entered
        if(username) {
            $.ajax({
                url: 'process_request_psswd.php',
                type: 'POST',
                data: { username: username },
                success: function(response) {
                    $('#loginMessage').html(`<p style="color: green;">${response.message}</p>`);
                },
                error: function() {
                    $('#loginMessage').html('<p style="color: red;">Failed to send reset link. Please try again.</p>');
                }
            });
        } else {
            $('#loginMessage').html('<p style="color: red;">Please enter your username to request a password reset.</p>');
        }
    });

    $('.HomeButton').click(function() {
        location.reload(); // Reload the page
    });

</script>
<?php
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>
