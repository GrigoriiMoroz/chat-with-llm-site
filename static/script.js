// ==================== DOM ELEMENT REFERENCES ====================
// Get references to HTML elements we'll need to interact with

const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-btn');

// ==================== HELPER FUNCTIONS ====================

/**
 * Add a message to the chat UI
 * @param {string} content - The message text to display
 * @param {boolean} isUser - True if message is from user, false if from bot
 */
function addMessage(content, isUser) {
    // Create a new div element for the message
    const messageDiv = document.createElement('div');

    // Add the base 'message' class and either
    // 'user-message' or 'bot-message'
    messageDiv.classList.add('message');
    messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');

    // Set the message content
    // For bot messages, add "Assistant:" prefix
    if (isUser) {
        messageDiv.textContent = content;
    } else {
        messageDiv.innerHTML = `<strong>Assistant:</strong> ${content}`;
    }

    // Add the message to the messages container
    messagesContainer.appendChild(messageDiv);

    // Auto-scroll to show the latest message
    // scrollTop = how far scrolled down
    // scrollHeight = total height of content
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Send a message to the backend and display the response
 */
async function sendMessage() {
    // Get the user's message from the input field
    const message = userInput.value.trim();

    // Don't send empty messages
    if (!message) {
        return;
    }

    // Add user message to the UI immediately
    addMessage(message, true);

    // Clear the input field
    userInput.value = '';

    try {
        // Send POST request to the /chat endpoint
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });

        // Check if the request was successful
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Parse the JSON response
        const data = await response.json();

        // Add the bot's response to the UI
        addMessage(data.response, false);

    } catch (error) {
        // If something goes wrong, show an error message
        console.error('Error:', error);
        addMessage(
            'Sorry, something went wrong. Please try again.',
            false
        );
    }
}

// ==================== EVENT LISTENERS ====================

// Listen for clicks on the Send button
sendButton.addEventListener('click', sendMessage);

// Listen for Enter key press in the input field
userInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

// ==================== INITIALIZATION ====================

console.log('Chat interface ready!');