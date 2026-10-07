
async function sendQuestion() {

    const input = document.getElementById("question");
    const chatBox = document.getElementById("chat-box");

    const question = input.value.trim();

    if (question === "") {
        return;
    }

    // Show user message
    chatBox.innerHTML += `
        <div class="user-message">
            <b>You:</b> ${question}
        </div>
    `;

    input.value = "";

    try {

        const response = await fetch("/ask", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })
        });

        const data = await response.json();

        // Convert simple Markdown formatting to HTML
        let answer = data.answer;

        answer = answer.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        answer = answer.replace(/\n/g, "<br>");

        // Show assistant response
        chatBox.innerHTML += `
            <div class="bot-message">
                <b>Assistant:</b>
                <div>${answer}</div>
            </div>
        `;

        // Show sources
        if (data.sources && data.sources.length > 0) {

            let sourcesHTML = "<b>Sources:</b><ul>";

            data.sources.forEach(source => {
                sourcesHTML += `
                    <li>${source.manual} — Page ${source.page}</li>
                `;
            });

            sourcesHTML += "</ul>";

            chatBox.innerHTML += `
                <div class="bot-message">
                    ${sourcesHTML}
                </div>
            `;
        }

    } catch (error) {

        chatBox.innerHTML += `
            <div class="bot-message">
                <b>Error:</b> Could not connect to the server.
            </div>
        `;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}
