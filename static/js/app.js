const { createApp, ref, onMounted } = Vue;

createApp({
    setup() {
        // Состояние UI
        const showAuthModal = ref(false);
        const showDetailsModal = ref(false);
        const isLoginForm = ref(true);
        const selectedAirport = ref(null);
        const nearestdAirport = ref(null);
        const passwordError = ref('');
        const loading = ref(true);
        const error = ref(null);
        const airports = ref([]);
        const airports_nearest = ref([])
        const userCity = ref(null);
        const geoLoading = ref(false);
        const geoError = ref(null);
        const showUserModal = ref(false);
        const userData = ref(null);
        const userLoading = ref(false);
        const accessToken = ref('');
        const latitude = ref(55.7522);
        const longitude = ref(37.6156);
        const distance = ref(null);
                         
        // Данные пользователя
        const isUser = ref(null);
        const authData = ref({
            name: '',
            email: '',
            password: '',
            confirmPassword: ''
        });


        // Методы
        const fetchUserData = async () => {
            try {
                userLoading.value = true;
                error.value = null;
                const token = localStorage.getItem('authToken');

                console.log("Данные jwt token for user:", {
                    token
                });
                
                const response = await fetch('http://localhost:8000/api/users/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    }
                });

                // Обработка HTTP ошибок
                if (!response.ok) {
                    const errorData = await response.json();
                    
                    if (response.status === 422) {
                        // Ошибка валидации данных
                        throw new Error('Некорректные данные: ' + 
                            (errorData.detail?.map?.(e => e.msg).join(', ') || errorData.detail));
                    } else if (response.status === 401) {
                        throw new Error('Необходимо заново авторизоваться');
                    } else {
                        throw new Error(errorData.detail || 'Ошибка сервера');
                    }
                }

                userData.value = await response.json();

                console.log("Данные полученные с сервера:", {
                    userData
                });
                
            } catch (err) {
                error.value = 'Ошибка загрузки данных. ' + err.message;
                console.error('Ошибка:', err);
            } finally {
                userLoading.value = false;
            }
         };

        const openUserModal = () => {
            showUserModal.value = true;
            if (!userData.value) {
                fetchUserData();
            }
        };

        // Отправка геоданных на сервер и получение города
        const sendGeoData = async (latitude, longitude) => {
            try {
                geoLoading.value = true;
                geoError.value = null;

                const params = new URLSearchParams({
                    latitude: latitude,
                    longitude: longitude
                });

                const response = await fetch(`http://localhost:8000/api/geo-local?${params.toString()}`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    }
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
                    latitude.value = position.coords.latitude;
                    longitude.value = position.coords.longitude;
                    sendGeoData(
                        latitude.value,
                        longitude.value
                    );
                },
                (err) => {
                    // При отсутствии данных передаем гео данные Москвы (установлены по умолчанию)
                    sendGeoData(
                        latitude.value,
                        longitude.value
                    );
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

        const showAirportDetails = async (airport) => {
            // Вычисляем расстояние от города(гео-точки пользователя) до выбранного аэропорта 
            const params = new URLSearchParams({
                latitude_city: latitude.value,
                longitude_city: longitude.value,
                latitude_airport: airport.latitude,
                longitude_airport: airport.longitude,
            });

            const response = await fetch(`http://localhost:8000/api/distance?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });
                            
            if (!response.ok) {
                throw new Error(`Ошибка: ${response.status}`);
            }
            
            const data = await response.json();

            // Сохраняем данные о расстоянии
            distance.value = {
                meters: data.distance_meters,
                kilometers: data.distance_kilometers
            };

            console.log("Данные о расстоянии:", distance.value);

            // Вычисляем расстояние от выбранного аэропорта() до ближайших 3х
            const params_airport = new URLSearchParams({
                latitude: airport.latitude,
                longitude: airport.longitude,
                limit: 3,
            });

            const response_nearest = await fetch(`http://localhost:8000/api/nearest?${params_airport.toString()}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });
                            
            if (!response_nearest.ok) {
                throw new Error(`Ошибка: ${response_nearest.status}`);
            }

            const data_nearest = await response_nearest.json();
            nearestdAirport.value = data_nearest;
            
            // airports_nearest.value = data_nearest;
            // console.log("Данные об аэропортах:", airports_nearest.value);

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


                // Сохранение данных пользователя
                isUser.value = {
                    name: user.full_name || authData.value.email.split('@')[0],
                    email: authData.value.email,
                    token: access_token
                };
                
        
                // Сохранение токена в localStorage
                localStorage.setItem('authToken', access_token);
                localStorage.setItem('Id', user.id);

                // Cookies.set('access_token', access_token, {
                //     secure: true,
                //     sameSite: 'strict'
                // });

                
                // Закрытие модального окна и сброс формы
                showAuthModal.value = false;
                authData.value = { name: '', email: '', password: '' };

                console.log('Успешная авторизация:', isUser.value.name);
        
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
            localStorage.setItem('Id', user.id);
            
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

        const logout = async () => {
            isUser.value = null;
            userData.value = null;
            showUserModal.value = false;

            localStorage.removeItem('authToken');
            // Cookies.remove('access_token');

            const response = await fetch('http://localhost:8000/api/users/logout');
                
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
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
            nearestdAirport,
            isUser,
            authData,
            passwordError,
            loading,
            error,
            airports,
            userCity,
            geoLoading,
            geoError,
            showUserModal,
            userData,
            userLoading,
            distance,
            airports_nearest,
            openUserModal,
            showAirportDetails,
            login,
            register,
            logout,
            fetchAirports
        };
    }
}).mount('#app');
