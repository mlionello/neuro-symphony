// Define questions and headers in both Italian and English
let questionsGoldsmi2 = {
    eng: {
        items: [
            "17. I am not able to sing in harmony when somebody is singing a familiar tune.",
            "18. I can tell when people sing or play out of time with the beat.",
            "19. I am able to identify what is special about a given musical piece.",
            "20. I am able to talk about the emotions that a piece of music evokes for me.",
            "21. I don’t spend much of my disposable income on music.",
            "22. I can tell when people sing or play out of tune.",
            "23. When I sing, I have no idea whether I’m in tune or not.",
            "24. Music is kind of an addiction for me - I couldn’t live without it.",
            "25. I don’t like singing in public because I’m afraid that I would sing wrong notes.",
            "26. When I hear a piece of music I can usually identify its genre.",
            "27. I would not consider myself a musician.",
            "28. I keep track of new music that I come across (e.g., new artists or recordings).",
            "29. After hearing a new song two or three times, I can usually sing it by myself.",
            "30. I only need to hear a new tune once and I can sing it back hours later.",
            "31. Music can evoke my memories of past people and places."
        ],
        header: [
            "Completely Disagree",
            "Strongly Disagree",
            "Disagree",
            "Neither Agree nor Disagree",
            "Agree",
            "Strongly Agree",
            "Completely Agree"
        ]
    },
    ita: {
        items: [
            "17. Quando qualcuno canta una melodia familiare, non so armonizzare (es. fare la seconda voce o il controcanto).",
            "18. Mi accorgo quando le persone cantano o suonano fuori tempo.",
            "19. So identificare quello che un determinato brano musicale ha di particolare.",
            "20. Sono in grado di parlare delle emozioni che un brano musicale mi suscita.",
            "21. Non spendo molto del mio reddito disponibile per cose musicali.",
            "22. Mi accorgo quando le persone cantano o suonano in modo stonato.",
            "23. Quando canto, non ho idea se io sia intonato/a oppure no.",
            "24. La musica è una sorta di dipendenza per me - non saprei vivere senza.",
            "25. Non mi piace cantare in pubblico perché temo che sbaglierei le note.",
            "26. Quando sento un brano, di solito sono in grado di identificare il suo genere musicale.",
            "27. Non mi considererei un/una musicista.",
            "28. Tengo traccia della nuova musica in cui mi imbatto (es. di nuovi artisti o di nuove registrazioni).",
            "29. Dopo aver sentito una canzone nuova per due o tre volte, di solito sono in grado di cantarla da solo/a.",
            "30. Mi basta sentire una melodia nuova una sola volta e riesco a ricantarla ore dopo.",
            "31. La musica mi evoca ricordi di persone e luoghi passati."
        ],
        header: [
            "Completamente in disaccordo",
            "Fortemente in disaccordo",
            "In disaccordo",
            "Né d’accordo né in disaccordo",
            "D'accordo",
            "Fortemente d'accordo",
            "Completamente d'accordo"
        ]
    }
};

let selectionQuestions = {
    ita : {
        init_text: [
            "32. Mi sono impegnato/a nella pratica regolare e quotidiana di uno strumento musicale (inclusa la voce) per ",
            "33. All’apice del mio interesse, mi sono esercitato/a per ",
            "34. Ho partecipato a ",
            "35. Ho ricevuto un’istruzione formale in teoria musicale per ",
            "36. Ho ricevuto un’istruzione formale in uno strumento musicale (inclusa la voce) per ",
            "37. So suonare ",
            "38. Ascolto musica con attenzione per ",
        ],
        end_text: [
            " anni.",
            " ore al giorno sul mio strumento principale.",
            " eventi musicali dal vivo come spettatore/spettatrice negli ultimi dodici mesi.",
            " anni.",
            " anni nel corso della mia vita.",
            " strumenti musicali.",
            " al giorno.",
        ],
        options: [
            ["0", "1", "2", "3", "4-5", "6-9", "10 o più"],
            ["0", "0.5", "1", "1.5", "2", "3-4", "5 o più"],
            ["0", "1", "2", "3", "4-6", "7-10", "11 o più"],
            ["0", "0.5", "1", "2", "3", "4-6", "7 o più"],
            ["0", "0.5", "1", "2", "3-5", "6-9", "10 o più"],
            ["0", "1", "2", "3", "4", "5", "6 o più"],
            ["0-15 minuti", "15-30 minuti", "30-60 minuti", "60-90 minuti", "2 ore", "3-5 ore", "4 ore o più"],
        ],
    }}

// Reference to the container
let containergoldsmi2 = document.getElementById('questions-containergoldsmi2');

lang = document.getElementById('lang').innerHTML; // Assuming this element contains the current language code
var debug = document.getElementById('debugContainer').value;

// Convert the value to a boolean (optional)
debug = (debug === "1");

// Populate the container with header and questions
containergoldsmi2.innerHTML += generateHeader(questionsGoldsmi2[lang].header); // Add the header

// Generate and insert questions based on the current language
let questions_goldmsi2 = questionsGoldsmi2[lang].items; // Select questions based on the current language
questions_goldmsi2.forEach((question, i) => {
    containergoldsmi2.innerHTML += generateQuestionHtml(question, 17 + i, 'q', 7, debug); // Use i + 1 to match the question numbering
});

// Append selection questions to the container
selectionQuestions["ita"].init_text.forEach((initText, index) => {
    let endText = selectionQuestions["ita"].end_text[index];
    let options = selectionQuestions["ita"].options[index];

    containergoldsmi2.innerHTML += generateSelectionQuestionHtml(initText, endText, options, index + 31 + 1, debug); // Start numbering from 32
});

containergoldsmi2.innerHTML += `<label for="q39" style="padding-right: 10px; margin: 0;">Lo strumento che suono meglio (compresa la voce) è</label>`;
if (debug) {
    containergoldsmi2.innerHTML += `<textarea id="q39" name="q39"  rows="1" cols="10" style="width: auto; margin:0"></textarea>`;
} else {
    containergoldsmi2.innerHTML += `<textarea id="q39" name="q39"  rows="1" cols="10" style="width: auto; margin:0" required></textarea>`;
}

// Function to generate the selection-based question HTML
function generateSelectionQuestionHtml(initText, endText, options, index, debug= false) {
    let backgroundColor = index % 2 === 0 ? 'rgba(240, 240, 240, 0.7)' : 'inherit'; // Light grey for even rows

    let questionHtml = `<div style="display: flex; align-items: center; padding:10px; background-color: ${backgroundColor}; min-height: 50px;">`;
    questionHtml += `<label for="q${index}" style="padding-right: 10px; margin: 0;">${initText}</label>`;

    // Add the dropdown for options
    if (debug) {
        questionHtml += `<select id="q${index}" name="q${index}" style="margin-right: 10px; width: auto">`;
    } else {
        questionHtml += `<select id="q${index}" name="q${index}" style="margin-right: 10px; width: auto" required>`;
    }
    questionHtml += `<option disabled selected value># ${endText}</option>`;
    options.forEach(option => {
        questionHtml += `<option value="${option}">${option} ${endText}</option>`;
    });
    questionHtml += `</select></div>`;

    return questionHtml;
}
