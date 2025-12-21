// Define questions and headers in both Italian and English
let questionsGoldsmi1 = {
    eng: {
        items: [
            "1. I spend a lot of my free time doing music-related activities.",
            "2. I sometimes choose music that can trigger shivers down my spine.",
            "3. I enjoy writing about music, for example on blogs and forums.",
            "4. If somebody starts singing a song I don’t know, I can usually join in.",
            "5. I am able to judge whether someone is a good singer or not.",
            "6. I usually know when I’m hearing a song for the first time.",
            "7. I can sing or play music from memory.",
            "8. I’m intrigued by musical styles I’m not familiar with and want to find out more.",
            "9. Pieces of music rarely evoke emotions for me.",
            "10. I am able to hit the right notes when I sing along with a recording.",
            "11. I find it difficult to spot mistakes in a performance of a song even if I know the tune.",
            "12. I can compare and discuss differences between two performances or versions of the same piece of music.",
            "13. I have trouble recognizing a familiar song when played in a different way or by a different performer.",
            "14. I have never been complimented for my talents as a musical performer.",
            "15. I often read or search the internet for things related to music.",
            "16. I often pick certain music to motivate or excite me.",
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
            "1. Trascorro molto del mio tempo libero a fare attività relative alla musica.",
            "2. A volte scelgo musica che mi fa venire i brividi lungo la schiena.",
            "3. Mi piace scrivere a proposito di musica, per esempio su blog o forum.",
            "4. Se qualcuno inizia a cantare una canzone che non conosco, di solito sono in grado di unirmi.",
            "5. Sono in grado di giudicare se qualcuno è un bravo cantante oppure no.",
            "6. Di solito so quando sto ascoltando una canzone per la prima volta.",
            "7. So cantare o suonare musica a memoria.",
            "8. Sono incuriosito/a da stili musicali a me non familiari e voglio saperne di più.",
            "9. È raro che brani musicali mi suscitino emozioni.",
            "10. Sono capace di prendere le note giuste quando canto su un brano registrato.",
            "11. Trovo difficile individuare gli errori in una performance di una canzone anche se conosco la melodia.",
            "12. So confrontare due performance o versioni dello stesso brano musicale e discutere delle loro differenze.",
            "13. Faccio fatica a riconoscere una canzone familiare quando è suonata in modo diverso o da un altro esecutore/esecutrice.",
            "14. Non ho mai ricevuto complimenti per il mio talento come performer musicale.",
            "15. Spesso leggo o cerco su internet cose relative alla musica.",
            "16. Spesso scelgo un certo tipo di musica per motivarmi o entusiasmarmi.",
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

// Reference to the container
let containergoldsmi1 = document.getElementById('questions-containergoldsmi1');

// Determine the language setting
lang = document.getElementById('lang').innerHTML; // Assuming this element contains the current language code
var debug = document.getElementById('debugContainer').value;

// Convert the value to a boolean (optional)
debug = (debug === "1");

// Populate the container with header and questions
containergoldsmi1.innerHTML += generateHeader(questionsGoldsmi1[lang].header); // Add the header

// Generate and insert questions based on the current language
let questions_goldmsi1 = questionsGoldsmi1[lang].items; // Select questions based on the current language
questions_goldmsi1.forEach((question, i) => {
    containergoldsmi1.innerHTML += generateQuestionHtml(question, i + 1, 'q', 7, debug); // Use i + 1 to match the question numbering
});
