function generateHeader(headerOptions, numcols = 7) {
    return `
        <div class="header_container" style="display: grid; grid-template-columns: 8fr repeat(${numcols}, 1fr);">
            <span></span> <!-- Empty span for the question labels -->
            ${headerOptions.map(option => `<span class="header_label">${option}</span>`).join('')}
        </div><br>
    `;
}

// Function to generate radio buttons for each question
function generateQuestionHtml(question, index, namePrefix = "q", numcols = 7, debug=false) {
    let backgroundColor = index % 2 === 0 ? 'rgba(240, 240, 240, 0.7)' : 'inherit'; // Light grey with 70% opacity for even rows

    let questionHtml = `<div style="display: grid; grid-template-columns: 8fr repeat(${numcols}, 1fr); align-items: center; background-color: ${backgroundColor}; min-height: 50px;"> 
        <label for="${namePrefix}${index}" style="padding: 10px; vertical-align: middle; margin: 0;">${question}</label>`;

    if (debug) { // If debug is true, make the inputs required
        for (let i = 1; i <= numcols; i++) {
            questionHtml += `<input type="radio" id="${namePrefix}${index}_${i}" name="${namePrefix}${index}" value="${i}" style="vertical-align: middle;">`;
        }
    } else { // If debug is false, inputs are not required
        for (let i = 1; i <= numcols; i++) {
            questionHtml += `<input type="radio" id="${namePrefix}${index}_${i}" name="${namePrefix}${index}" value="${i}" style="vertical-align: middle;" required>`;
        }
    }

    questionHtml += `</div>`;
    return questionHtml;
}
