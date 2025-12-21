// Define questions and header options in both Italian and English
questions_dict = {
    ita: {
        questions: [
            "Quanto ti è piaciuta la musica?",
            "Quanto ti sei sentito coinvolto emotivamente durante l'ascolto complessivo?",
            "Quanto è stato difficile interpretare il significato delle etichette dei bottoni?",
            "Quanto è stato difficile associare le etichette dei bottoni all'ascolto?",
            "Quanto è stato difficile gestire molteplici bottoni?",
            "La musica ascoltata mi era familiare",
        ],
        header: [
            "Per niente", "Molto poco", "Poco", "Moderatamente", "Abbastanza", "Molto", "Estremamente",
        ],
    },
    eng: {
        questions: [
            "How much did you enjoy the music?",
            "How much did you feel emotionally involved during the entire listening?"
        ],
        header: [
            "Not at all", "Very mild", "Mild", "Moderately", "Fairly enough", "Very much", "Extremely",
        ]
    }
};

lang = document.getElementById('lang').innerHTML;
debug = document.getElementById('debugContainer').value;

// Convert the value to a boolean (optional)
debug = (debug === "1");
// Reference to the containers
questions_container = document.getElementById('post_experiment_setquestion1');
sub_question_dict1 = questions_dict[lang].questions; // Select questions based on the current language

questions_container.innerHTML += generateHeader(questions_dict[lang].header, 7); // Add the header
sub_question_dict1.forEach((question, i) => {
    questions_container.innerHTML += generateQuestionHtml(question, i + 1, 'q1_', 7, debug);
});

questions_container.innerHTML += `<br><br><label for="recon_auth" style="padding-right: 10px; margin: 0;">Ho riconosciuto il compositore</label>
<input type="radio" id="recon_auth_yes" name="recon_auth" value="no"> No
<input  type = "radio"  id = "recon_auth_no"  name = "recon_auth"  value = "yes" > Sì`;
questions_container.innerHTML += `<br><label for="recon_auth" style="padding-right: 10px; margin: 0;">Se sì, nome del compositore:</label>
<input type="text" name="recon_auth_value" id="recon_auth_name" name="recon_auth_name" style="width: 200px; height: 22px"><br><br>`;

questions_container.innerHTML += `<br><label for="recon_work" style="padding-right: 10px; margin: 0;">Ho riconosciuto l'opera dell'autore</label>
<input type="radio" id="recon_work_yes" name="recon_work" value="no"> No
<input  type = "radio"  id = "recon_work_no"  name = "recon_work"  value = "yes" > Sì`;
questions_container.innerHTML += `<br><label for="recon_auth" style="padding-right: 10px; margin: 0;">Se sì, nome della composizione:</label>
<input type="text" name="recon_work_value" id="recon_work_name" name="recon_work_name" style="width: 200px; height: 22px">`;
