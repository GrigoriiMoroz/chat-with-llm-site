// ==================== ССЫЛКИ НА DOM ЭЛЕМЕНТЫ ====================
// Получаем ссылки на HTML элементы, с которыми будем взаимодействовать

const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-btn');

// ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

/**
 * Добавить сообщение в UI чата
 * @param {string} content - Текст сообщения для отображения
 * @param {boolean} isUser - True если сообщение от пользователя, false если от бота
 */
function addMessage(content, isUser) {
    // Создаём новый div элемент для сообщения
    const messageDiv = document.createElement('div');

    // Добавляем базовый класс 'message' и либо
    // 'user-message' или 'bot-message'
    messageDiv.classList.add('message');
    messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');

    // Устанавливаем содержимое сообщения
    // Для сообщений бота добавляем префикс "Assistant:"
    if (isUser) {
        messageDiv.textContent = content;
    } else {
        messageDiv.innerHTML = `<strong>Assistant:</strong> ${content}`;
    }

    // Добавляем сообщение в контейнер сообщений
    messagesContainer.appendChild(messageDiv);

    // Автоматическая прокрутка для показа последнего сообщения
    // scrollTop = насколько прокручено вниз
    // scrollHeight = общая высота контента
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Отправить сообщение на backend и отобразить ответ
 */
async function sendMessage() {
    // Получаем сообщение пользователя из поля ввода
    const message = userInput.value.trim();

    // Не отправляем пустые сообщения
    if (!message) {
        return;
    }

    // Добавляем сообщение пользователя в UI сразу
    addMessage(message, true);

    // Очищаем поле ввода
    userInput.value = '';

    try {
        // Отправляем POST запрос на эндпоинт /chat
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });

        // Проверяем, был ли запрос успешным
        if (!response.ok) {
            throw new Error(`HTTP ошибка! статус: ${response.status}`);
        }

        // Парсим JSON ответ
        const data = await response.json();

        // Добавляем ответ бота в UI
        addMessage(data.response, false);

    } catch (error) {
        // Если что-то пошло не так, показываем сообщение об ошибке
        console.error('Ошибка:', error);
        addMessage(
            'Извините, что-то пошло не так. Попробуйте снова.',
            false
        );
    }
}

// ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

// Слушаем клики на кнопку Send
sendButton.addEventListener('click', sendMessage);

// Слушаем нажатие клавиши Enter в поле ввода
userInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

console.log('Интерфейс чата готов!');