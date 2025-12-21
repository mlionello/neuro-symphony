<?php
session_start();
$token = $_GET['token'] ?? '';
$username = $_GET['username'] ?? '';

// Ensure both token and username are present and token has the correct length
if (empty($token) || empty($username) || strlen($token) != 32) {
    echo "Invalid request";
    exit;
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Password</title>
</head>
<body>
    <div id="resetpsswdcontainer">
        <h1>Reset Your Password</h1>
        <form id="resetPasswordForm">
            <input type="hidden" name="token" value="<?php echo htmlspecialchars($token); ?>">
            <input type="hidden" name="username" value="<?php echo htmlspecialchars($username); ?>">
            <label for="newPassword">New Password:</label>
            <input type="password" id="newPassword" name="newPassword" required>
            <br><br>
            <div id="resetpsswdMessage"></div>
            <button id="submitupdatepassword" type="submit">Reset Password</button>
        </form>
    </div>
<script src="../js/jquery-3.7.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/js-sha1/build/sha1.min.js"></script>
<script>
    $(document).ready(function () {
        $('#resetPasswordForm').submit(function (event) {
            event.preventDefault();  // Prevent the traditional submission of the form
            var newPassword = $('#newPassword').val();
            var hashedPassword = sha1(newPassword);
            var prefix = hashedPassword.substr(0, 5);
            var suffix = hashedPassword.substr(5).toUpperCase();

            $.get('https://api.pwnedpasswords.com/range/' + prefix, function(data) {
                var lines = data.split('\n');
                var compromised = lines.some(function(line) {
                    var parts = line.split(':');
                    return parts[0] === suffix;
                });

                if (compromised) {
                    $('#resetpsswdMessage').html(`<p style='color:red'>The new password is too weak. Please, choose a different one.</p>`);
                } else {
                    var formData = $('#resetPasswordForm').serialize();  // Serialize form data within the handler
                    $.ajax({
                        url: 'update_password.php',
                        method: 'POST',
                        dataType: 'json',
                        data: formData,
                        success: function (response) {
                            if (response.success) {
                                let countdown = 5;
                                $('#resetpsswdcontainer').html(response.content + `<br><p> You will be redirected to the home page in <span id="countdown">${countdown}</span> seconds...</p>`);
                                let interval = setInterval(function () {
                                    countdown--;
                                    $('#countdown').text(countdown);
                                    if (countdown <= 0) {
                                        clearInterval(interval);
                                        window.location.href = 'https://neuro-symphony.com';
                                    }
                                }, 1000);
                            } else {
                                alert('Failed to reset password: ' + response.error);
                            }
                        },
                        error: function () {
                            alert('Error contacting server.');
                        }
                    });
                }
            }, 'text');
        });
    });
</script>

</body>
</html>
