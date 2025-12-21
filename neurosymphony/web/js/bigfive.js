// Define questions and headers in both Italian and English
let questionsbigfive = {
    eng: {
        items: [
            "... is reserved",
            "... is generally trusting",
            "... tends to be lazy",
            "... is relaxed, handles stress well",
            "... has few artistic interests",
            "... is outgoing, sociable",
            "... tends to find fault with others",
            "... does a thorough job",
            "... gets nervous easily",
            "... has an active imagination",
        ],
        header: [
            "Disagree strongly",
            "Disagree a little",
            "Neither agree nor disagree",
            "Agree a little",
            "Agree strongly",
        ]
    },
    ita: {
        items: [
            "... è riservata",
            "... generalmente si fida",
            "... tende ad essere pigra",
            "... è rilassata, sopporta bene lo stress",
            "... ha pochi interessi artistici",
            "... è spigliata, socievole",
            "... tende a trovare difetti negli altri",
            "... è coscienziosa nel lavoro",
            "... si agita facilmente",
            "... ha una fervida immaginazione",
        ],
        header: [
            "Fortemente in disaccordo",
            "In disaccordo",
            "Né d’accordo né in disaccordo",
            "D'accordo",
            "Fortemente d'accordo"
        ]
    }
};

// Reference to the container
let containerbigfive = document.getElementById('questions-containerbigfive');

// Determine the language setting
lang = document.getElementById('lang').innerHTML; // Assuming this element contains the current language code
var debug = document.getElementById('debugContainer').value;

// Convert the value to a boolean (optional)
debug = (debug === "1");

// Populate the container with header and questions
containerbigfive.innerHTML += generateHeader(questionsbigfive[lang].header, 5); // Add the header

// Generate and insert questions based on the current language
let questions_bigfive = questionsbigfive[lang].items; // Select questions based on the current language
questions_bigfive.forEach((question, i) => {
    containerbigfive.innerHTML += generateQuestionHtml(question, i + 1, 'q', 5, debug); // Use i + 1 to match the question numbering
});
