// Define questions and options in both Italian and English
questions_dict = {
    ita: {
        questionswho5: [
            "1. Mi sono sentito/a allegro/a e di buon umore.",
            "2. Mi sono sentito/a calmo/a e rilassato/a.",
            "3. Mi sono sentito/a attivo/a e energico/a.",
            "4. Mi sono svegliato/a sentendomi fresco/a e riposato/a.",
            "5. La mia vita di tutti i giorni è stata piena di cose che mi interessano."
        ],
        header: [
            "Sempre",
            "La maggior parte del tempo",
            "Più della metà del tempo",
            "Meno della metà del tempo",
            "A volte",
            "Mai"
        ]
    },
    eng: {
        questionswho5: [
            "1. I have felt cheerful in good spirits.",
            "2. I have felt calm and relaxed.",
            "3. I have felt active and vigorous.",
            "4. I woke up feeling fresh and rested.",
            "5. My daily life has been filled with things that interest me."
        ],
        header: [
            "All of the time",
            "Most of the time",
            "More than half the time",
            "Less than half the time",
            "Some of the time",
            "At no time"
        ]
    }
};

// Determine the language setting
lang = document.getElementById('lang').innerHTML; // Assuming this element contains the current language code
debug = document.getElementById('debugContainer').value;

// Convert the value to a boolean (optional)
debug = (debug === "1");

// Reference to the container
questions_container = document.getElementById('questions-containerwho5');

// Populate the container with header and questions
questions_container.innerHTML += generateHeader(questions_dict[lang].header, 6); // Add the header

// Generate and insert questions based on the current language
sub_question_dict1 = questions_dict[lang].questionswho5; // Select questions based on the current language
sub_question_dict1.forEach((question, i) => {
    questions_container.innerHTML += generateQuestionHtml(question, i, 'q', 6, debug); // Use i + 1 to match the question numbering
});

if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
    } else if (document.documentElement.mozRequestFullScreen) { // Firefox
        document.documentElement.mozRequestFullScreen();
    } else if (document.documentElement.webkitRequestFullscreen) { // Chrome, Safari and Opera
        document.documentElement.webkitRequestFullscreen();
    } else if (document.documentElement.msRequestFullscreen) { // IE/Edge
        document.documentElement.msRequestFullscreen();
    }