const { createApp, ref, onMounted } = Vue;

createApp({
    setup() {
        // Состояние UI
        const showAuthModal = ref(false);
        const showDetailsModal = ref(false);
        const isLoginForm = ref(true);
        const selectedAirport = ref(null);
        const passwordError = ref('');
        const loading = ref(true);
        const error = ref(null);
        const airports = ref([]);
        const userCity = ref(null);
        const geoLoading = ref(false);
        const geoError = ref(null);
        
        // Данные пользователя
        const isUser = ref(null);
        const authData = ref({
            name: '',
            email: '',
            password: '',
            confirmPassword: ''
        });


        // Методы
        // Отправка геоданных на сервер и получение города
        const sendGeoData = async (latitude, longitude) => {
            try {
                geoLoading.value = true;
                geoError.value = null;
                
                const response = await fetch('http://localhost:8000/api/geo-local', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        latitude: latitude,
                        longitude: longitude
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Ошибка: ${response.status}`);
                }
                
                const data = await response.json();
                userCity.value = data.city || 'Неизвестный город';
                
            } catch (err) {
                geoError.value = err.message;
                console.error('Ошибка геолокации:', err);
            } finally {
                geoLoading.value = false;
            }
        };

        // Получение геолокации пользователя
        const getUserLocation = () => {
            if (!navigator.geolocation) {
                geoError.value = "Геолокация не поддерживается";
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    sendGeoData(
                        position.coords.latitude,
                        position.coords.longitude
                    );
                },
                (err) => {
                    geoError.value = "Доступ к геолокации запрещен";
                    console.warn("Ошибка геолокации:", err.message);
                },
                { 
                    enableHighAccuracy: true,
                    timeout: 5000
                }
            );
        };


        const fetchAirports = async () => {
            try {
                loading.value = true;
                error.value = null;
                
                // Используем стандартный fetch вместо axios
                const response = await fetch('http://localhost:8000/api/airport');
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                airports.value = data;

                console.log("Данные полученные с сервера:", {
                    data
                });
                
            } catch (err) {
                error.value = 'Ошибка загрузки данных. ' + err.message;
                console.error('Ошибка:', err);
            } finally {
                loading.value = false;
            }
        };

        const showAirportDetails = (airport) => {
            selectedAirport.value = airport;
            showDetailsModal.value = true;
        };

        const login = async () => {
            try {
                // Валидация данных перед отправкой
                if (!authData.value.email || !authData.value.password) {
                    throw new Error('Email и пароль обязательны для заполнения');
                }
        
                // Отправка запроса к FastAPI бэкенду
                const response = await fetch('http://localhost:8000/api/users/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        username: authData.value.email,  // FastAPI обычно ожидает 'username' для email
                        password: authData.value.password
                    })
                });
        
                // Обработка HTTP ошибок
                if (!response.ok) {
                    const errorData = await response.json();
                    
                    if (response.status === 422) {
                        // Ошибка валидации данных
                        throw new Error('Некорректные данные: ' + 
                            (errorData.detail?.map?.(e => e.msg).join(', ') || errorData.detail));
                    } else if (response.status === 401) {
                        throw new Error('Неверные учетные данные: ' + 
                            (errorData.detail?.map?.(e => e.msg).join(', ') || errorData.detail));
                       // throw new Error('Неверные учетные данные');
                    } else {
                        throw new Error(errorData.detail || 'Ошибка сервера');
                    }
                }
        
                // Успешный ответ
                const { access_token, token_type, user } = await response.json();

                // Выводим в консоль полученные данные
                console.log("Данные полученные с сервера:", {
                    access_token,
                    token_type,
                    user
                });


                // Сохранение данных пользователя
                isUser.value = {
                    name: user.full_name || authData.value.email.split('@')[0],
                    email: authData.value.email,
                    token: access_token
                };
                
        
                // Сохранение токена в localStorage
                localStorage.setItem('authToken', access_token);
                
                // Закрытие модального окна и сброс формы
                showAuthModal.value = false;
                authData.value = { name: '', email: '', password: '' };

                console.log('Успешная авторизация:', isUser.value);
        
            } catch (error) {
                console.error('Login error:', error);
                alert(error.message || 'Произошла ошибка при входе');
            }
        };

        const register = async () => {
            if (authData.value.password !== authData.value.confirmPassword) {
                passwordError.value = 'Пароли не совпадают';
                return
            }
            console.log('Успешная регистрация:', passwordError.value);

            try {
                // Отправка запроса к FastAPI бэкенду
                const response = await fetch('http://localhost:8000/api/users/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    username: authData.value.name,  
                    email: authData.value.email,
                    password: authData.value.password
                })
            });

            // Обработка HTTP ошибок
            if (!response.ok) {
                const errorData = await response.json();
                
                if (response.status === 422) {
                    // Ошибка валидации данных
                    throw new Error('Некорректные данные: ' + 
                        (errorData.detail?.map?.(e => e.msg).join(', ') || errorData.detail));
                } else if (response.status === 401) {
                    throw new Error('Неверные учетные данные: ' + 
                        (errorData.detail?.map?.(e => e.msg).join(', ') || errorData.detail));
                    // throw new Error('Неверные учетные данные');
                } else {
                    throw new Error(errorData.detail || 'Ошибка сервера');
                }
            }

            // Успешный ответ
            const { access_token, token_type, user } = await response.json();


            // Сохранение данных пользователя
            isUser.value = {
                name: user.full_name || authData.value.email.split('@')[0],
                email: authData.value.email,
                token: access_token
            };
                
    
            // Сохранение токена в localStorage
            localStorage.setItem('authToken', access_token);
            
            // Закрытие модального окна и сброс формы
            showAuthModal.value = false;
            authData.value = { name: '', email: '', password: '', confirmPassword: '' };
    
            console.log('Успешная регистрация:', isUser.value);
            showAuthModal.value = false;

            } catch (error) {
                console.error('Login error:', error);
                alert(error.message || 'Произошла ошибка при регистрации');
            } finally {
                isLoginForm.value = true;
            }
        };

        const logout = () => {
            isUser.value = null;
            localStorage.removeItem('authToken');
        };

        // Загружаем данные сразу при запуске
        onMounted(() => {
            getUserLocation();
            fetchAirports();
        });  

        return {
            showAuthModal,
            showDetailsModal,
            isLoginForm,
            selectedAirport,
            isUser,
            authData,
            passwordError,
            loading,
            error,
            airports,
            userCity,
            geoLoading,
            geoError,
            showAirportDetails,
            login,
            register,
            logout,
            fetchAirports
        };
    }
}).mount('#app');
