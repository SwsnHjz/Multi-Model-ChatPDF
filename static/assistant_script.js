document.addEventListener('DOMContentLoaded', () => {
    const assistantWidget = document.getElementById('assistant-widget');
    if (!assistantWidget) return; 

    const assistantToggleButton = document.getElementById('assistant-toggle-button');
    
    if (assistantToggleButton) {
        assistantToggleButton.addEventListener('click', () => {
            const userStatus = assistantToggleButton.dataset.userStatus;

            if (userStatus === 'logged-in') {
                assistantWidget.classList.toggle('widget-hidden');
            } else {
                const loginButton = document.getElementById('login-modal-button');
                if (loginButton) {
                    loginButton.click();
                }
            }
        });
    }
    
    const closeButton = document.getElementById('assistant-close-button');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            assistantWidget.classList.add('widget-hidden');
        });
    }
    
    const messageContainer = document.getElementById('assistant-messages');
    const assistantForm = document.getElementById('assistant-form');
    const assistantInput = document.getElementById('assistant-input');
    const headerText = assistantWidget.querySelector('.assistant-widget-header h4');
    const sendButton = assistantWidget.querySelector('.assistant-widget-form button');
    const mainLangToggle = document.getElementById('lang-toggle');

    
    
    
    const assistantTranslations = {
        en: {
            header: "Help Assistant",
            placeholder: "Ask about this site...",
            send: "Send",
            initial_greeting: "Hello! I'm the site assistant. Ask me questions about how this site works."
        },
        ar: {
            header: "مساعد",
            placeholder: "اسأل عن الموقع...",
            send: "إرسال",
            initial_greeting: "مرحباً! أنا مساعد الموقع. اسألني عن كيفية عمل هذا الموقع."
        }
    };
    function applyLanguage(lang) {
        const T = assistantTranslations[lang] || assistantTranslations['en'];
        headerText.textContent = T.header;
        assistantInput.placeholder = T.placeholder;
        sendButton.textContent = T.send;
        if (messageContainer.children.length === 1 && messageContainer.querySelector('.bot-message')) {
            messageContainer.children[0].textContent = T.initial_greeting;
        }
    }
    function addMessageToChat(sender, content, type = 'text') {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        if (type === 'html') {
            messageDiv.innerHTML = content;
        } else if (content.includes('@')) {
            messageDiv.innerHTML = content.replace(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/g, '<a href="mailto:$1">$1</a>');
        } else {
            messageDiv.textContent = content;
        }
        messageContainer.appendChild(messageDiv);
        messageContainer.scrollTop = messageContainer.scrollHeight;
        return messageDiv;
    }
    
    assistantForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userQuestion = assistantInput.value.trim();
        if (!userQuestion) return;

        addMessageToChat('user', userQuestion);
        assistantInput.value = '';
        const thinkingIndicatorHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
        const thinkingDiv = addMessageToChat('bot', thinkingIndicatorHTML, 'html');

        try {
            const currentLang = localStorage.getItem('lang') || 'en';
            const response = await fetch(ASSISTANT_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: userQuestion,
                    lang: currentLang
                })
            });
            if (!response.ok) throw new Error('Server error');
            const data = await response.json();
            if(thinkingDiv) thinkingDiv.remove();
            addMessageToChat('bot', data.answer);
        } catch (error) {
            console.error("Error asking assistant:", error);
            if(thinkingDiv) thinkingDiv.remove();
            addMessageToChat('bot', 'An error occurred. Please try again.');
        }
    });

    
    assistantWidget.classList.add('widget-hidden');
    addMessageToChat('bot', assistantTranslations.en.initial_greeting);
    if (mainLangToggle) {
        const checkLang = () => {
            const currentLang = localStorage.getItem('lang') || 'en';
            applyLanguage(currentLang);
        };
        checkLang();
        mainLangToggle.addEventListener('click', () => {
            setTimeout(checkLang, 10); 
        });
    }
});