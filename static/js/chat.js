document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    // Generate a unique chat ID for this session
    const chatId = generateChatId();
    
    // Add event listeners
    sendButton.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
    
    // Handle sending messages
    async function handleSend() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Disable input while processing
        setInputState(false);
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        userInput.value = '';
        
        try {
            // Show loading indicator
            const loadingId = addLoadingIndicator();
            
            // Send message to API
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    chat_id: chatId
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get response from server');
            }
            
            const data = await response.json();
            
            // Remove loading indicator
            removeLoadingIndicator(loadingId);
            
            // Add assistant's response to chat
            addMessage(data.response, 'assistant');
            
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, I encountered an error while processing your request. Please try again.', 'assistant');
        } finally {
            // Re-enable input
            setInputState(true);
        }
    }
    
    // Add a message to the chat
    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add loading indicator
    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant-message';
        loadingDiv.id = 'loading-indicator';
        
        const loadingSpinner = document.createElement('div');
        loadingSpinner.className = 'loading';
        
        loadingDiv.appendChild(loadingSpinner);
        chatMessages.appendChild(loadingDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return 'loading-indicator';
    }
    
    // Remove loading indicator
    function removeLoadingIndicator(id) {
        const loadingDiv = document.getElementById(id);
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
    
    // Set input state (enabled/disabled)
    function setInputState(enabled) {
        userInput.disabled = !enabled;
        sendButton.disabled = !enabled;
    }
    
    // Generate a unique chat ID
    function generateChatId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Add welcome message
    addMessage('Hello! I can help you search through Federal Registry documents. What would you like to know?', 'assistant');
});
