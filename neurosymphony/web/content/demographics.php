<?php
header('Content-Type: application/json');
include '../content/demographics_multi_lang.php';

if (isset($_SESSION['debug'])) {
    $debug = $_SESSION['debug'];
} else {$_SESSION['debug']=false; $debug=false;}

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['error' => 'Session expired or not set. Please restart the experiment.']);
    http_response_code(401); // Unauthorized
    exit;
}
$_SESSION['step'] = 'demographics';

$lang = $_SESSION["lang"] ?? 'eng';

// Prepare HTML content to be returned
ob_start(); // Start output buffering
?>
<div id="trackCounter" class="track-counter"><?php echo ($_SESSION["lang"]=="ita") ? 'questionario ' : 'questionnaire '; echo '1/4'?></div>
<h1><?php echo $demo_transl['title'][$lang]; ?></h1>
<form id="demographics-form" class="submit-and-proceed" method="post" style="width:auto">
    <input type="hidden" name="current_section" value="demographics">

    <label for="age"><?php echo $demo_transl['age_label'][$lang]; ?></label>
    <select id="age" name="age" <?php echo (!$debug ? 'required' : ''); ?> >
        <option disabled selected value><?php echo $demo_transl['highest_education_options']['disabled'][$lang]; ?></option>
    </select><br><br>

    <label for="gender"><?php echo $demo_transl['gender_label'][$lang]; ?></label>
    <select id="gender" name="gender" <?php echo (!$debug ? 'required' : ''); ?>>
        <option disabled selected value><?php echo $demo_transl['gender_options']['disabled'][$lang]; ?></option>
        <option value="man"><?php echo $demo_transl['gender_options']['man'][$lang]; ?></option>
        <option value="woman"><?php echo $demo_transl['gender_options']['woman'][$lang]; ?></option>
        <option value="nb"><?php echo $demo_transl['gender_options']['nb'][$lang]; ?></option>
        <option value="other"><?php echo $demo_transl['gender_options']['other'][$lang]; ?></option>
        <option value="prefer_not_to_say"><?php echo $demo_transl['gender_options']['prefer_not_to_say'][$lang]; ?></option>
    </select><br><br>

    <label for="highest_education"><?php echo $demo_transl['highest_education_label'][$lang]; ?></label><br>
    <select id="highest_education" name="highest_education" <?php echo (!$debug ? 'required' : ''); ?>>
        <option disabled selected value><?php echo $demo_transl['highest_education_options']['disabled'][$lang]; ?></option>
        <option value="primary_school"><?php echo $demo_transl['highest_education_options']['primary_school'][$lang]; ?></option>
        <option value="secondary_school"><?php echo $demo_transl['highest_education_options']['secondary_school'][$lang]; ?></option>
        <option value="undergraduate"><?php echo $demo_transl['highest_education_options']['undergraduate'][$lang]; ?></option>
        <option value="postgraduate"><?php echo $demo_transl['highest_education_options']['postgraduate'][$lang]; ?></option>
        <option value="phd"><?php echo $demo_transl['highest_education_options']['phd'][$lang]; ?></option>
    </select><br><br>

    <label for="occupation"><?php echo $demo_transl['occupation_label'][$lang]; ?></label><br>
    <select id="occupation" name="occupation" <?php echo (!$debug ? 'required' : ''); ?>>
        <option disabled selected value><?php echo $demo_transl['occupation_options']['disabled'][$lang]; ?></option>
        <option value="student"><?php echo $demo_transl['occupation_options']['student'][$lang]; ?></option>
        <option value="full_time"><?php echo $demo_transl['occupation_options']['full_time'][$lang]; ?></option>
        <option value="part_time"><?php echo $demo_transl['occupation_options']['part_time'][$lang]; ?></option>
        <option value="self_employed"><?php echo $demo_transl['occupation_options']['self_employed'][$lang]; ?></option>
        <option value="homemaker"><?php echo $demo_transl['occupation_options']['homemaker'][$lang]; ?></option>
        <option value="unemployed"><?php echo $demo_transl['occupation_options']['unemployed'][$lang]; ?></option>
        <option value="retired"><?php echo $demo_transl['occupation_options']['retired'][$lang]; ?></option>
    </select><br><br>

    <label for="childhood_country"><?php echo $demo_transl['country_labels']['childhood'][$lang]; ?></label><br>
    <select id="childhood_country" name="childhood_country" <?php echo (!$debug ? 'required' : ''); ?>>
        <option disabled selected value><?php echo $demo_transl['occupation_options']['disabled'][$lang]; ?></option>
    </select><br><br>

    <label for="mother_tongue"><?php echo $demo_transl['mother_tongue'][$lang]; ?></label><br>
    <select id="mother_tongue" name="mother_tongue" <?php echo (!$debug ? 'required' : ''); ?>>
        <option disabled selected value><?php echo $demo_transl['occupation_options']['disabled'][$lang]; ?></option>
    </select><br><br>

    <label for="psychiatric_treatment"><?php echo $demo_transl['psy']['psychiatric_treatment'][$lang]; ?></label>
    <input type="radio" id="psychiatric_treatment_yes" name="psychiatric_treatment" value="yes" <?php echo (!$debug ? 'required' : ''); ?>> <?php echo ($_SESSION["lang"]=="ita") ? 'Sì ' : 'Yes '; ?>
    <input type="radio" id="psychiatric_treatment_no" name="psychiatric_treatment" value="no"> <?php echo ($_SESSION["lang"]=="ita") ? 'No ' : 'No '; ?><br><br>

    <label for="psychiatric_diagnosis"><?php echo $demo_transl['psy']['psychiatric_diagnosis'][$lang]; ?></label>
    <input type="radio" id="psychiatric_diagnosis_yes" name="psychiatric_diagnosis" value="yes" <?php echo (!$debug ? 'required' : ''); ?>> <?php echo ($_SESSION["lang"]=="ita") ? 'Sì ' : 'Yes '; ?>
    <input type="radio" id="psychiatric_diagnosis_no" name="psychiatric_diagnosis" value="no"> <?php echo ($_SESSION["lang"]=="ita") ? 'No ' : 'No '; ?><br><br>

    <button type="submit"><?php echo $demo_transl['submit_button'][$lang]; ?></button>
</form>
<script src="../js/demographics.js" defer></script>
<?php
$htmlContent = ob_get_clean(); // Capture the HTML content
echo json_encode(['success' => true, 'content' => $htmlContent]); // Return the content as JSON
?>
