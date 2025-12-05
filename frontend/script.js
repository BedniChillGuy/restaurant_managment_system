const API_BASE = '/api';
let currentUser = null;
let token = localStorage.getItem('token');
let dishes = [];
let selectedItems = [];
let selectedTableNumber = localStorage.getItem('selectedTableNumber') || null;
let editingOrderId = null;
let editSelectedItems = [];

// Утилиты
function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.form').forEach(form => form.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(`${tabName}-form`).classList.add('active');
}

function showScreen(screenName) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.add('hidden');
    });
    document.getElementById(screenName).classList.remove('hidden');
}

function showInterface(role) {
    document.querySelectorAll('.interface').forEach(iface => {
        iface.classList.add('hidden');
    });
    document.getElementById(`${role}-interface`).classList.remove('hidden');

    // Добавляем кнопку удаления аккаунта, если её ещё нет
}

function showModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}


// Функция для показа пользовательских сообщений об ошибках
function showError(message, error = null) {
    console.error('Ошибка:', message, error);

    // Словарь человеческих сообщений об ошибках
    const errorMessages = {
        'Session expired': 'Ваша сессия истекла. Пожалуйста, войдите снова.',
        'Incorrect username or password': 'Неверный логин или пароль',
        'Username already registered': 'Пользователь с таким именем уже существует',
        'Password must be at least 4 characters': 'Пароль должен содержать минимум 4 символа',
        'Password cannot be empty': 'Пароль не может быть пустым',
        'Only administrators can view users': 'Только администраторы могут просматривать пользователей',
        'Cannot delete your own account': 'Вы не можете удалить свою собственную учетную запись',
        'User not found': 'Пользователь не найден',
        'You can only change your own password': 'Вы можете изменить только свой собственный пароль',
        'Only administrators can transfer orders': 'Только администраторы могут передавать заказы',
        'Order not found': 'Заказ не найден',
        'New waiter not found': 'Новый официант не найден',
        'Only administrators can update restaurant config': 'Только администраторы могут изменять конфигурацию ресторана',
        'Total tables must be between 1 and 100': 'Количество столов должно быть от 1 до 100',
        'Only administrators can create dishes': 'Только администраторы могут добавлять блюда',
        'Dish not found': 'Блюдо не найдено',
        'Only administrators can delete dishes': 'Только администраторы могут удалять блюда',
        'Only waiters can create orders': 'Только официанты могут создавать заказы',
        'Table not found': 'Стол не найден',
        'Table is not available': 'Стол занят',
        'You can only view your own orders': 'Вы можете просматривать только свои заказы',
        'You can only update your own orders': 'Вы можете обновлять только свои заказы',
        'Only administrators can delete orders': 'Только администраторы могут удалять заказы',
        'Failed to fetch': 'Не удалось подключиться к серверу. Проверьте подключение к интернету.',
        'NetworkError when attempting to fetch resource': 'Ошибка сети. Проверьте подключение к интернету.',
        'Cannot delete the last administrator account': 'Нельзя удалить последнюю учетную запись администратора',
        'Cannot delete admin account with assigned orders': 'Невозможно удалить аккаунт администратора с привязанными заказами',
        'Internal Server Error': 'Внутренняя ошибка сервера. Попробуйте позже.',
        'Username must be at least 3 characters': 'Имя пользователя должно содержать минимум 3 символа',
        'Username cannot exceed 50 characters': 'Имя пользователя не может превышать 50 символов',
        'Username cannot be empty': 'Имя пользователя не может быть пустым',
        'Role must be either \'admin\' or \'waiter\'': 'Роль должна быть "admin" или "waiter"',
        'Dish name cannot be empty': 'Название блюда не может быть пустым',
        'Dish name cannot exceed 100 characters': 'Название блюда не может превышать 100 символов',
        'Price must be greater than 0': 'Цена должна быть больше 0',
        'Price is too high': 'Цена слишком высока',
        'Quantity must be greater than 0': 'Количество должно быть больше 0',
        'Quantity cannot exceed 100': 'Количество не может превышать 100',
        'Value error, Password must be at least 4 characters': 'Пароль должен содержать минимум 4 символа',
        'Value error, Password cannot be empty': 'Пароль не может быть пустым',
        'Value error, Username must be at least 3 characters': 'Имя пользователя должно содержать минимум 3 символа',
        'Value error, Username cannot exceed 50 characters': 'Имя пользователя не может превышать 50 символов',
        'Value error, Username cannot be empty': 'Имя пользователя не может быть пустым',
        'Value error, Dish name cannot be empty': 'Название блюда не может быть пустым',
        'Value error, Dish name cannot exceed 100 characters': 'Название блюда не может превышать 100 символов',
        'Value error, Price must be greater than 0': 'Цена должна быть больше 0',
        'Value error, Price is too high': 'Цена слишком высока',
        'Value error, Quantity must be greater than 0': 'Количество должно быть больше 0',
        'Value error, Quantity cannot exceed 100': 'Количество не может превышать 100',
        "Value error, Role must be either 'admin' or 'waiter'": 'Роль должна быть "admin" или "waiter"'
    };

    // Ищем человеческое сообщение
    let humanMessage = errorMessages[message];

    if (!humanMessage && error) {
        // Если есть детали ошибки от сервера, пытаемся их обработать
        if (error.detail) {
            if (Array.isArray(error.detail)) {
                humanMessage = error.detail.map(d => d.msg || d.message).join(', ');
            } else if (typeof error.detail === 'string') {
                humanMessage = errorMessages[error.detail] || error.detail;
            } else if (error.detail.message) {
                humanMessage = error.detail.message;
            }
        } else if (error.message) {
            humanMessage = errorMessages[error.message] || error.message;
        }
    }

    // Если не нашли человеческое сообщение, используем оригинальное
    if (!humanMessage) {
        humanMessage = message || 'Произошла неизвестная ошибка';
    }

    alert(humanMessage);
}

// API функции
function showDeleteAccountModal() {
    if (!currentUser) {
        showError('Пользователь не авторизован');
        return;
    }

    let message = 'Вы уверены, что хотите удалить свой аккаунт? Это действие нельзя отменить.';

    if (currentUser.role === 'waiter') {
        message += '<br><br>Ваши активные заказы будут переданы другому официанту. Если других официантов нет, заказы будут удалены.';
    } else if (currentUser.role === 'admin') {
        message += '<br><br>Это возможно только если в системе есть другие администраторы.';
    }

    document.getElementById('delete-account-message').innerHTML = message;
    showModal('delete-account-modal');
}


function confirmAccountDeletion() {
    deleteOwnAccount();
}


async function apiCall(endpoint, options = {}) {
    const controller = new AbortController();
    const timeout = options.timeout || 30000; // 30 секунд по умолчанию для длительных операций
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    console.log(`Отправка запроса: ${API_BASE}${endpoint}`, options.body ? JSON.parse(options.body) : '');

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers,
            ...options,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        console.log(`Статус ответа: ${response.status}`);

        if (response.status === 422) {
            const errorData = await response.json();
            console.error('Ошибка валидации:', errorData);
            
            // Извлекаем сообщения об ошибках валидации
            let validationErrors = [];
            if (Array.isArray(errorData.detail)) {
                validationErrors = errorData.detail.map(err => {
                    // Pydantic возвращает ошибки в формате {loc: [...], msg: "...", type: "..."}
                    return err.msg || err.message || 'Ошибка валидации';
                });
            } else if (typeof errorData.detail === 'string') {
                validationErrors = [errorData.detail];
            }
            
            // Берём первое сообщение об ошибке
            const errorMessage = validationErrors[0] || 'Ошибка валидации данных';
            throw new Error(errorMessage);
        }

        if (response.status === 401) {
            // Пытаемся получить детали ошибки из ответа
            let errorText;
            try {
                const clone = response.clone();
                const errorData = await clone.json();
                errorText = errorData.detail || errorData.message || 'Необходима авторизация';
            } catch {
                errorText = 'Необходима авторизация';
            }
            
            // Если токен истек (это НЕ ошибка логина), выходим
            if (token && errorText !== 'Incorrect username or password') {
                logout();
                throw new Error('Session expired');
            }
            
            console.error(`HTTP 401: ${errorText}`);
            throw new Error(errorText);
        }

        if (!response.ok) {
            let errorText;
            try {
                const clone = response.clone();
                const errorData = await clone.json();
                errorText = errorData.detail || errorData.message || `HTTP error! status: ${response.status}`;
            } catch {
                errorText = await response.text();
            }

            console.error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            throw new Error(errorText);
        }

        // Для DELETE запросов может не быть тела
        if (response.status === 204 || options.method === 'DELETE') {
            return { success: true };
        }

        const data = await response.json();
        console.log('Получены данные:', data);
        return data;

    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            showError('Запрос превысил время ожидания. Операция может занять некоторое время. Попробуйте еще раз.');
        } else {
            console.error('API call failed:', error);
            showError(error.message, error);
        }
        throw error;
    }
}

// Аутентификация
async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showError('Заполните все поля');
        return;
    }

    try {
        const result = await apiCall('/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        if (result && result.access_token) {
            token = result.access_token;
            currentUser = result.user;
            localStorage.setItem('token', token);
            startApp();
        }
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

let changingPasswordUserId = null;

// Функции для работы с модальным окном смены пароля
function openChangePasswordModal() {
    if (!currentUser) {
        showError('Пользователь не авторизован');
        return;
    }

    changingPasswordUserId = currentUser.id;
    document.getElementById('new-password').value = '';
    document.getElementById('confirm-password').value = '';
    showModal('change-password-modal');
}

function closePasswordModal() {
    closeModal('change-password-modal');
    changingPasswordUserId = null;
}

async function confirmPasswordChange() {
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    if (!newPassword || !confirmPassword) {
        showError('Заполните все поля');
        return;
    }

    if (newPassword !== confirmPassword) {
        showError('Пароли не совпадают');
        return;
    }

    try {
        await apiCall(`/users/${changingPasswordUserId}/password`, {
            method: 'PUT',
            body: JSON.stringify({ new_password: newPassword })
        });

        alert('Пароль успешно изменен');
        closePasswordModal();
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    const role = document.getElementById('reg-role').value;

    if (!username || !password) {
        showError('Заполните все поля');
        return;
    }

    try {
        const result = await apiCall('/register', {
            method: 'POST',
            body: JSON.stringify({ username, password, role })
        });

        if (result) {
            alert('Регистрация успешна! Теперь войдите в систему.');
            showTab('login');
            document.getElementById('reg-username').value = '';
            document.getElementById('reg-password').value = '';
        }
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    showScreen('auth-screen');
}

// Основное приложение
async function startApp() {
    if (token) {
        try {
            const userResult = await apiCall('/me');
            if (userResult) {
                currentUser = userResult;
            }
        } catch (error) {
            console.error('Failed to get user info:', error);
            logout();
            return;
        }
    }

    if (!currentUser) {
        showScreen('auth-screen');
        return;
    }

    showScreen('main-screen');

    const userRoleElement = document.getElementById('user-role');
    if (userRoleElement) {
        userRoleElement.textContent = `Роль: ${currentUser.role === 'admin' ? 'Администратор' : 'Официант'}`;
    }

    showInterface(currentUser.role);
    await loadData();

    if (currentUser.role === 'admin') {
        setInterval(loadData, 5000);
    }
}

async function loadData() {
    try {
        dishes = await apiCall('/dishes') || [];

        if (currentUser.role === 'admin') {
            await loadTables();
            await loadUsers();
            await loadDishes();
            await loadOrders();
        } else {
            await loadAvailableTables();
            await loadMenu();
            await loadCurrentOrders();
        }
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

// Функции для работы со столами
async function loadTables() {
    try {
        const tables = await apiCall('/tables') || [];
        const container = document.getElementById('tables-container');
        if (!container) return;

        container.innerHTML = tables.map(table => `
            <div class="table-card ${table.is_available ? 'available' : 'occupied'}">
                <h4>Стол #${table.number}</h4>
                <p>Статус: ${table.is_available ? 'Свободен' : 'Занят'}</p>
                ${table.current_order_id ? `<p>Заказ: #${table.current_order_id}</p>` : ''}
            </div>
        `).join('');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

async function updateTableConfig() {
    const totalTables = document.getElementById('total-tables').value;
    if (!totalTables) {
        showError('Введите количество столов');
        return;
    }

    try {
        await apiCall('/restaurant/config', {
            method: 'PUT',
            body: JSON.stringify({ total_tables: parseInt(totalTables) })
        });

        document.getElementById('total-tables').value = '';
        await loadTables();
        alert('Данные о столах были обновлены');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

// Функции администратора
async function loadUsers() {
    try {
        const users = await apiCall('/users') || [];
        const container = document.getElementById('users-container');
        if (!container) return;

        container.innerHTML = users.map(user => `
            <div class="user-card">
                <h4>${user.username}</h4>
                <p>Роль: ${user.role === 'admin' ? 'Администратор' : 'Официант'}</p>
                <div class="user-actions">
                    ${user.id !== currentUser.id && user.role !== 'admin' ?
                        `<button class="danger-btn" onclick="deleteUser(${user.id})">Удалить</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

let currentTransferOrderId = null;

// Функция открытия модального окна передачи заказа
async function openTransferOrderModal(orderId, currentWaiterId = null) {
    currentTransferOrderId = orderId;

    try {
        // Получаем объект заказа для отображения кода
        const order = await apiCall(`/orders/${orderId}`);
        
        // Получаем список всех официантов
        const allUsers = await apiCall('/users') || [];
        const waiters = allUsers.filter(user => user.role === 'waiter' && user.id !== currentWaiterId);

        const waiterSelect = document.getElementById('transfer-waiter-select');
        waiterSelect.innerHTML = '<option value="">Выберите официанта</option>';

        if (waiters.length === 0) {
            waiterSelect.innerHTML = '<option value="">Нет доступных официантов</option>';
            waiterSelect.disabled = true;
        } else {
            waiters.forEach(waiter => {
                const option = document.createElement('option');
                option.value = waiter.id;
                option.textContent = waiter.username;
                waiterSelect.appendChild(option);
            });
            waiterSelect.disabled = false;
        }

        document.getElementById('transfer-order-id').textContent = order ? (order.code || order.id) : orderId;
        showModal('transfer-order-modal');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

// Функция подтверждения передачи
async function confirmTransfer() {
    const waiterSelect = document.getElementById('transfer-waiter-select');
    const newWaiterId = waiterSelect.value;

    if (!newWaiterId) {
        showError('Выберите официанта для передачи заказа');
        return;
    }

    if (!currentTransferOrderId) {
        showError('Ошибка: не указан заказ для передачи');
        return;
    }

    try {
        const result = await apiCall(`/orders/${currentTransferOrderId}/transfer?new_waiter_id=${newWaiterId}`, {
            method: 'PUT'
        });

        alert(result.message || `Заказ #${currentTransferOrderId} успешно передан!`);
        closeTransferModal();
        await loadOrders();

        // Если мы в интерфейсе официанта, обновляем и его заказы
        if (currentUser.role === 'waiter') {
            await loadCurrentOrders();
        }
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

// Функция закрытия модального окна передачи
function closeTransferModal() {
    closeModal('transfer-order-modal');
    currentTransferOrderId = null;
    document.getElementById('transfer-waiter-select').innerHTML = '<option value="">Выберите официанта</option>';
}

async function deleteUser(userId) {
    if (!confirm('Удалить этого пользователя? Это может занять несколько секунд.')) {
        return;
    }

    const button = event.target;
    const originalText = button.textContent;

    try {
        button.textContent = 'Удаление...';
        button.disabled = true;

        const result = await apiCall(`/users/${userId}`, {
            method: 'DELETE',
            timeout: 45000
        });

        if (result && result.message) {
            alert(result.message);
            await loadUsers();
            await loadOrders();
            await loadTables();
        }
    } catch (error) {
        // Восстанавливаем кнопку при ошибке
        button.textContent = originalText;
        button.disabled = false;
    }
    // При успешном удалении кнопка пересоздается в loadUsers(), так что не нужно восстанавливать
}


async function loadDishes() {
    try {
        const container = document.getElementById('dishes-container');
        if (!container) return;

        container.innerHTML = dishes.map(dish => `
            <div class="dish-card">
                <h4>${dish.name}</h4>
                <p>${dish.description}</p>
                <p>Цена: ${dish.price} руб.</p>
                <button onclick="deleteDish(${dish.id})">Удалить</button>
            </div>
        `).join('');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

async function addDish() {
    const name = document.getElementById('dish-name').value;
    const description = document.getElementById('dish-desc').value;
    const price = parseFloat(document.getElementById('dish-price').value);

    if (!name || !description || !price) {
        showError('Заполните все поля');
        return;
    }

    try {
        await apiCall('/dishes', {
            method: 'POST',
            body: JSON.stringify({ name, description, price })
        });

        document.getElementById('dish-name').value = '';
        document.getElementById('dish-desc').value = '';
        document.getElementById('dish-price').value = '';
        await loadData();
        alert('Блюдо успешно добавлено!');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

async function deleteDish(dishId) {
    if (confirm('Удалить это блюдо?')) {
        try {
            await apiCall(`/dishes/${dishId}`, { method: 'DELETE' });
            await loadData();
            alert('Блюдо успешно удалено');
        } catch (error) {
            // Ошибка уже обработана в apiCall
        }
    }
}

async function loadOrders() {
    try {
        const orders = await apiCall('/orders') || [];
        const container = document.getElementById('orders-container');
        if (!container) return;

        container.innerHTML = orders.map(order => `
        <div class="order-card">
            <h4>Заказ ${order.code ? '#' + order.code : '#' + order.id} (Стол ${order.table_number})</h4>
            <p>Блюда: ${order.items.map(item => `${item.dish_name} x${item.quantity}`).join(', ')}</p>
            <p>Статус: <span class="status-${order.status}">${getStatusText(order.status)}</span></p>
            <p>Официант: ${order.waiter_name}</p>
            <p>Создан: ${new Date(order.created_at).toLocaleString()}</p>
            <div class="order-actions">
                <button class="danger-btn" onclick="deleteOrder(${order.id})">Отменить заказ</button>
                <button class="transfer-btn" onclick="openTransferOrderModal(${order.id}, ${order.waiter_id})">Передать заказ</button>
            </div>
        </div>
    `).join('');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

// Функция удаления заказа
async function deleteOrder(orderId) {
    if (!confirm('Вы уверены, что хотите отменить этот заказ? Это действие нельзя отменить.')) {
        return;
    }

    try {
        const result = await apiCall(`/orders/${orderId}`, {
            method: 'DELETE'
        });

        if (result && result.message) {
            alert('Заказ успешно отменен!');
            await loadOrders();
            await loadTables();
        }
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

// Функции официанта
async function loadMenu() {
    try {
        const container = document.getElementById('menu-items');
        if (!container) return;

        container.innerHTML = dishes.filter(dish => dish.available).map(dish => `
            <div class="menu-item" onclick="selectDish(${dish.id})">
                <h4>${dish.name}</h4>
                <p>${dish.description}</p>
                <p>Цена: ${dish.price} руб.</p>
            </div>
        `).join('');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

function selectDish(dishId) {
    const dish = dishes.find(d => d.id === dishId);
    if (!dish) return;

    const existingItem = selectedItems.find(item => item.dish_id === dishId);

    if (existingItem) {
        existingItem.quantity++;
    } else {
        selectedItems.push({
            dish_id: dishId,
            quantity: 1,
            dish: dish
        });
    }

    updateSelectedItems();
}

function updateSelectedItems() {
    const container = document.getElementById('selected-items');
    if (!container) return;

    container.innerHTML = selectedItems.map((item, index) => `
        <div class="order-item">
            <span>${item.dish.name} x${item.quantity}</span>
            <span>${(item.dish.price * item.quantity).toFixed(2)} руб.</span>
            <button onclick="removeItem(${index})">Удалить</button>
        </div>
    `).join('');
}

function removeItem(index) {
    selectedItems.splice(index, 1);
    updateSelectedItems();
}

async function createOrder() {
    const tableNumber = document.getElementById('table-select').value;

    if (!tableNumber || selectedItems.length === 0) {
        showError('Выберите стол и добавьте блюда');
        return;
    }

    const order = {
        table_number: parseInt(tableNumber),
        items: selectedItems.map(item => ({
            dish_id: item.dish_id,
            quantity: item.quantity
        }))
    };

    try {
        await apiCall('/orders', {
            method: 'POST',
            body: JSON.stringify(order)
        });

        selectedItems = [];
        document.getElementById('table-select').value = '';
        updateSelectedItems();
        await loadAvailableTables();
        await loadCurrentOrders();
        alert('Заказ создан успешно!');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

async function loadCurrentOrders() {
    try {
        const orders = await apiCall('/orders') || [];
        const container = document.getElementById('current-orders');
        if (!container) return;

        container.innerHTML = orders.map(order => `
            <div class="order-card">
                <h4>Заказ ${order.code ? '#' + order.code : '#' + order.id} (Стол ${order.table_number})</h4>
                <p>Блюда: ${order.items.map(item => `${item.dish_name} x${item.quantity}`).join(', ')}</p>
                <p>Статус: <span class="status-${order.status}">${getStatusText(order.status)}</span></p>
                <p>Создан: ${new Date(order.created_at).toLocaleString()}</p>
                <select onchange="updateOrderStatus(${order.id}, this.value)">
                    <option value="pending" ${order.status === 'pending' ? 'selected' : ''}>Ожидает</option>
                    <option value="preparing" ${order.status === 'preparing' ? 'selected' : ''}>Готовится</option>
                    <option value="ready" ${order.status === 'ready' ? 'selected' : ''}>Готов</option>
                    <option value="completed" ${order.status === 'completed' ? 'selected' : ''}>Завершен</option>
                </select>
                <button onclick="openEditOrderModal(${order.id})">Редактировать</button>
            </div>
        `).join('');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

// Редактирование заказов
async function openEditOrderModal(orderId) {
    try {
        const order = await apiCall(`/orders/${orderId}`);
        if (!order) return;

        editingOrderId = orderId;
        editSelectedItems = [...order.items];

        document.getElementById('edit-order-id').textContent = order.code || order.id;
        document.getElementById('edit-order-status').value = order.status;

        // Загружаем доступные столы для редактирования
        const tables = await apiCall('/tables/available') || [];
        const allTables = await apiCall('/tables') || [];
        const availableTables = [...tables, allTables.find(t => t.number === order.table_number)].filter(Boolean);

        const tableSelect = document.getElementById('edit-table-select');
        tableSelect.innerHTML = '<option value="">Выберите стол</option>' +
            availableTables.map(table => `
                <option value="${table.number}" ${table.number === order.table_number ? 'selected' : ''}>
                    Стол #${table.number}
                </option>
            `).join('');

        updateEditSelectedItems();
        showModal('edit-order-modal');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

function closeEditModal() {
    closeModal('edit-order-modal');
    editingOrderId = null;
    editSelectedItems = [];
}

function removeEditItem(index) {
    editSelectedItems.splice(index, 1);
    updateEditSelectedItems();
}

function openAddDishModal() {
    const container = document.getElementById('add-dish-list');
    if (!container) return;

    container.innerHTML = dishes.filter(dish => dish.available).map(dish => `
        <div class="menu-item" onclick="addDishToEditOrder(${dish.id})">
            <h4>${dish.name}</h4>
            <p>${dish.description}</p>
            <p>Цена: ${dish.price} руб.</p>
        </div>
    `).join('');

    showModal('add-dish-modal');
}

function closeAddDishModal() {
    closeModal('add-dish-modal');
}

function addDishToEditOrder(dishId) {
    const dish = dishes.find(d => d.id === dishId);
    if (!dish) return;

    const existingItem = editSelectedItems.find(item => item.dish_id === dishId);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        editSelectedItems.push({
            dish_id: dishId,
            quantity: 1,
            dish_name: dish.name,
            dish_price: dish.price
        });
    }

    updateEditSelectedItems();
    closeAddDishModal();
}

function updateEditSelectedItems() {
    const container = document.getElementById('edit-selected-items');
    if (!container) return;

    container.innerHTML = editSelectedItems.map((item, index) => {
        const dish = dishes.find(d => d.id === item.dish_id) || {
            name: item.dish_name || 'Неизвестное блюдо',
            price: item.dish_price || 0
        };

        return `
            <div class="order-item">
                <div>
                    <strong>${dish.name}</strong>
                    <br>
                    <span>Количество: ${item.quantity} | Цена: ${dish.price * item.quantity} руб.</span>
                </div>
                <div>
                    <button onclick="increaseDishQuantity(${index})">+</button>
                    <button onclick="decreaseDishQuantity(${index})">-</button>
                    <button onclick="removeEditItem(${index})">Удалить</button>
                </div>
            </div>
        `;
    }).join('');
}

function increaseDishQuantity(index) {
    if (editSelectedItems[index]) {
        editSelectedItems[index].quantity += 1;
        updateEditSelectedItems();
    }
}

function decreaseDishQuantity(index) {
    if (editSelectedItems[index] && editSelectedItems[index].quantity > 1) {
        editSelectedItems[index].quantity -= 1;
        updateEditSelectedItems();
    }
}

async function saveOrderChanges() {
    if (!editingOrderId) return;

    const tableNumber = document.getElementById('edit-table-select').value;
    const status = document.getElementById('edit-order-status').value;

    if (!tableNumber) {
        showError('Выберите стол');
        return;
    }

    const orderUpdate = {
        table_number: parseInt(tableNumber),
        status: status,
        items: editSelectedItems
    };

    try {
        await apiCall(`/orders/${editingOrderId}`, {
            method: 'PUT',
            body: JSON.stringify(orderUpdate)
        });

        closeEditModal();
        await loadCurrentOrders();
        await loadAvailableTables();
        alert('Заказ успешно обновлен!');
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

// Общие функции
async function updateOrderStatus(orderId, status) {
    try {
        await apiCall(`/orders/${orderId}/status?status=${status}`, { method: 'PUT' });
        await loadCurrentOrders();
        if (currentUser.role === 'admin') {
            await loadOrders();
        }
        await loadAvailableTables();
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}

function getStatusText(status) {
    const statuses = {
        'pending': 'Ожидает',
        'preparing': 'Готовится',
        'ready': 'Готов',
        'completed': 'Завершен'
    };
    return statuses[status] || status;
}

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    showScreen('auth-screen');

    if (token) {
        try {
            const userResult = await apiCall('/me');
            if (userResult) {
                currentUser = userResult;
                startApp();
            }
        } catch (error) {
            console.error('Auto-login failed:', error);
            localStorage.removeItem('token');
        }
    }
});

async function loadAvailableTables() {
    try {
        const allTables = await apiCall('/tables') || [];
        const tables = allTables.filter(t => t.is_available);

        const tableSelect = document.getElementById('table-select');
        if (tableSelect) {
            const previousValue = selectedTableNumber || localStorage.getItem('selectedTableNumber');
            tableSelect.innerHTML = '<option value="">Выберите стол</option>' + tables.map(table => `
                <option value="${table.number}">Стол #${table.number}</option>
            `).join('');
            if (previousValue) {
                tableSelect.value = previousValue;
            }

            tableSelect.addEventListener('change', (e) => {
                selectedTableNumber = e.target.value;
                if (selectedTableNumber) {
                    localStorage.setItem('selectedTableNumber', selectedTableNumber);
                } else {
                    localStorage.removeItem('selectedTableNumber');
                }
            });
        }

        const tablesContainer = document.getElementById('waiter-tables-container');
        if (tablesContainer) {
            tablesContainer.innerHTML = allTables.map(table => `
                <div class="table-card ${table.is_available ? 'available' : 'occupied'}">
                    <h4>Стол #${table.number}</h4>
                    <p>Статус: ${table.is_available ? 'Свободен' : 'Занят'}</p>
                </div>
            `).join('');
        }
    } catch (error) {
        // Ошибка уже обработана в apiCall
    }
}
async function deleteOwnAccount() {
    if (!currentUser) {
        showError('Пользователь не авторизован');
        return;
    }

    try {
        // Получаем кнопку из модального окна
        const button = document.querySelector('#delete-account-modal .danger-btn');
        const originalText = button.textContent;

        button.textContent = 'Удаление...';
        button.disabled = true;

        const result = await apiCall('/me', {
            method: 'DELETE',
            timeout: 45000
        });

        // Закрываем модальное окно в любом случае
        closeModal('delete-account-modal');

        if (result && result.message) {
            alert(result.message);
            logout(); // Выход и перезагрузка страницы
        }
    } catch (error) {
        // Всегда закрываем модальное окно при ошибке
        closeModal('delete-account-modal');
        // Ошибка уже обработана в apiCall, но модальное окно закрыто
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');

    // Всегда восстанавливаем кнопку удаления аккаунта при закрытии модального окна
    if (modalId === 'delete-account-modal') {
        const button = document.querySelector('#delete-account-modal .danger-btn');
        if (button) {
            button.textContent = 'Удалить аккаунт';
            button.disabled = false;
        }
    }
}