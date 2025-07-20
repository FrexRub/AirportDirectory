const { createApp, ref, onMounted, computed, nextTick } = Vue;

createApp({
    setup() {
//        const baseURL = 'http://localhost:8000';
         const baseURL = '';

        // Состояние UI
        const showAuthModal = ref(false);
        const showDetailsModal = ref(false);
        const isLoginForm = ref(true);
        const selectedAirport = ref(null);
        const nearestdAirport = ref(null);
        const nearestAirportsCity = ref(null);
        const nearestAirportsLoading = ref(false);
        const passwordError = ref('');
        const userCity = ref(null);
        const geoLoading = ref(false);
        const geoError = ref(null);
        const showUserModal = ref(false);
        const userData = ref(null);
        const resendLoading = ref(false);
        const resendSuccess = ref(false);
        const userLoading = ref(false);
        const accessToken = ref('');
        const latitude = ref(55.7522);
        const longitude = ref(37.6156);
        const distance = ref(null);
        const airports = ref({ items: [], total: 0, page: 1, size: 12 });
        const currentPage = ref(1);
        const totalPages = ref(1);
        const loading = ref(false);
        const error = ref(null);
        const localTime = ref('');
        const citySearch = ref('');
        const cities = ref(window.externalCities || []);


        // Данные пользователя
        const isUser = ref(null);
        const authData = ref({
            name: '',
            email: '',
            password: '',
            confirmPassword: ''
        });


        // Методы

        // Фильтрация городов по поисковому запросу
        const filteredCities = computed(() => {
            if (!citySearch.value) return cities.value;
            return cities.value.filter(city =>
                city.toLowerCase().includes(citySearch.value.toLowerCase())
            );
        });

        // Открытие модального окна
        const openCityModal = () => {
            const modal = new bootstrap.Modal(document.getElementById('citySelectModal'));
            modal.show();
            nextTick(() => {
                document.querySelector('#citySelectModal input').focus();
            });
        };

        // Выбор города
        const selectCity = async (city) => {
            try {
                userCity.value = city;
                // Сохраняем в localStorage
                localStorage.setItem('selectedCity', city);

                // получение данных о городе
                const params_by_id = new URLSearchParams({
                    title: city,
                });

                const response = await fetch(`${baseURL}/api/city?${params_by_id.toString()}`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error(`Ошибка: ${response.status}`);
                }

                const city_info = await response.json();

                console.log("Данные о городе:", city_info);

                latitude.value = city_info.latitude;
                longitude.value = city_info.longitude;
                console.log("Новые координаты:", latitude.value, longitude.value);
                getNearestAirports();

                // Закрываем модальное окно
                const modal = bootstrap.Modal.getInstance(document.getElementById('citySelectModal'));
                modal.hide();
                // Очищаем поиск
                citySearch.value = '';
            } catch (error) {
                console.error("Произошла ошибка при выборе города:", error);
            }
        };

        // Выбор первого города в списке
        const selectFirstCity = () => {
            if (filteredCities.value.length > 0) {
                selectCity(filteredCities.value[0]);
            }
        };


        const fetchUserData = async () => {
            try {
                userLoading.value = true;
                error.value = null;
                const token = localStorage.getItem('authToken');

                const response = await fetch(`${baseURL}/api/users/me`, {
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

                console.log("Данные пользователя (userData) полученны с сервера:");

            } catch (err) {
                error.value = 'Ошибка загрузки данных. ' + err.message;
                console.error('Ошибка:', err);
            } finally {
                userLoading.value = false;
            }
         };

        const openUserModal = () => {
            showUserModal.value = true;

            if (!userData.value || (userData.value && !userData.value.is_verified)) {
                fetchUserData();
            }
        };

        // Отправка геоданных на сервер и получение города
        const sendGeoData = async (latitude, longitude) => {
            try {
                console.log("Start sendGeoData", latitude, longitude)
                geoLoading.value = true;
                geoError.value = null;

                const params = new URLSearchParams({
                    latitude: latitude,
                    longitude: longitude
                });

                const response = await fetch(`${baseURL}/api/geo-local?${params.toString()}`, {
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
            console.log("Start getUserLocation", latitude.value, longitude.value)
            if (!navigator.geolocation) {
                geoError.value = "Геолокация не поддерживается";
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    latitude.value = position.coords.latitude;
                    longitude.value = position.coords.longitude;
                    console.log("Set geolocat", latitude.value, longitude.value);
                    sendGeoData(
                        latitude.value,
                        longitude.value
                    );
                    getNearestAirports();
                },
                (err) => {
                    // При отсутствии данных передаем гео данные Москвы (установлены по умолчанию)
                    console.log("Error geolocat", latitude.value, longitude.value);
                    sendGeoData(
                        latitude.value,
                        longitude.value
                    );
                    getNearestAirports();
                },
                {
                    enableHighAccuracy: true,
                    timeout: 5000
                }
            );
        };


        const fetchAirports = async (page = 1) => {
            try {
                loading.value = true;
                error.value = null;

                // Используем стандартный fetch вместо axios
                const response = await fetch(`${baseURL}/api/airports?page=${page}&size=12`);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                airports.value = data.items;
                currentPage.value = data.page;
                totalPages.value = data.pages;

                console.log("Данные полученные с сервера:", { data });
                console.log('Current:', currentPage.value, 'Total:', totalPages.value, 'Items:', data.items.length)

            } catch (err) {
                error.value = 'Ошибка загрузки данных. ' + err.message;
                console.error('Ошибка:', err);
            } finally {
                loading.value = false;
            }
        };

        // Переход на предыдущую страницу
        const prevPage = () => {
            if (currentPage.value > 1) {
                fetchAirports(currentPage.value - 1);
            }
        };

        // Переход на следующую страницу
        const nextPage = () => {
            if (currentPage.value < totalPages.value) {
                fetchAirports(currentPage.value + 1);
            }
        };

        // Переход на конкретную страницу
        const goToPage = (page) => {
            fetchAirports(page);
        };


        const showAirportDetails = async (airport) => {
            // получение данных об аэропрте
            const params_by_id = new URLSearchParams({
                id: airport.id,
            });

            const response_by_id = await fetch(`${baseURL}/api/airport?${params_by_id.toString()}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response_by_id.ok) {
                throw new Error(`Ошибка: ${response_by_id.status}`);
            }

            const airport_by_id = await response_by_id.json();

            console.log("Данные об аэропрте:", airport_by_id);

            // Вычисляем расстояние от города(гео-точки пользователя) до выбранного аэропорта
            const params = new URLSearchParams({
                latitude_city: latitude.value,
                longitude_city: longitude.value,
                latitude_airport: airport_by_id.latitude,
                longitude_airport: airport_by_id.longitude,
            });

            const response = await fetch(`${baseURL}/api/distance?${params.toString()}`, {
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
                latitude: airport_by_id.latitude,
                longitude: airport_by_id.longitude,
                limit: 3,
            });

            const response_nearest = await fetch(`${baseURL}/api/nearest?${params_airport.toString()}`, {
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

            selectedAirport.value = airport_by_id;
            showDetailsModal.value = true;
        };

        const login = async () => {
            try {
                // Валидация данных перед отправкой
                if (!authData.value.email || !authData.value.password) {
                    throw new Error('Email и пароль обязательны для заполнения');
                }

                // Отправка запроса к FastAPI бэкенду
                const response = await fetch(`${baseURL}/api/users/login`, {
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

                if (!user.is_verified) {
                    alert('Вы не подтвердили свою почту. Подтвердите её в своем ЛК (кликните на свое имя).');
                }

                // Сохранение данных пользователя
                isUser.value = {
                    name: user.full_name || authData.value.email.split('@')[0],
                    email: authData.value.email,
                    token: access_token
                };

                // Сохранение токена в localStorage
                localStorage.setItem('authToken', access_token);
                localStorage.setItem('Id', user.id);
                console.log('Успешная авторизация:', isUser.value.name);

                // Cookies.set('access_token', access_token, {
                //     secure: true,
                //     sameSite: 'strict'
                // });

                // Закрытие модального окна и сброс формы
                showAuthModal.value = false;
                authData.value = { name: '', email: '', password: '' };

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
                const response = await fetch(`${baseURL}/api/users/register`, {
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

            alert('На вашу почту направлено письмо для завершения регистрации!');

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

            const response = await fetch(`${baseURL}/api/users/logout`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        };


        // метод получения ближайших аэропортов
        async function getNearestAirports() {
            nearestAirportsLoading.value = true;
            try {
           // Вычисляем расстояние от текущего города до трех ближайших аэропортов
            console.log("Start getNearestAirports", latitude.value, longitude.value)
            const params_city = new URLSearchParams({
                latitude: latitude.value,
                longitude: longitude.value,
                limit: 3,
            });

            const response_nearest_city = await fetch(`${baseURL}/api/nearest?${params_city.toString()}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response_nearest_city.ok) {
                throw new Error(`Ошибка: ${response_nearest_city.status}`);
            }

            const data_nearest_city = await response_nearest_city.json();
            nearestAirportsCity.value = data_nearest_city;


            console.log("Данные о ближайших к городу аэропортах получены:", nearestAirportsCity.value);


            } catch (error) {
                console.error('Ошибка при загрузке ближайших аэропортов:', error);
            } finally {
                nearestAirportsLoading.value = false;
            }
        }

        // Функция для форматирования местного времени
        const formatLocalTime = (timeZone) => {
            try {
                const options = {
                    timeZone: timeZone,
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                };
                return new Date().toLocaleTimeString('ru-RU', options);
            } catch (e) {
                console.error('Ошибка формата времени:', e);
                return 'недоступно';
            }
        };

        const resendVerificationEmail = async () => {
                resendLoading.value = true;
                resendSuccess.value = false;

                try {
                    const token = localStorage.getItem('authToken');

                    const response = await fetch(`${baseURL}/api/users/mail_confirm`, {
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

                    // Успешный ответ
                    const data = await response.json();
                    const accessToken = data.access_token;

                    // Сохранение токена в localStorage
                    localStorage.setItem('authToken', accessToken);
                    console.log('Отпрака писмь для подтверждения:');

                    resendSuccess.value = true;

                    // Автоматически скрываем сообщение через 5 секунд
                    setTimeout(() => {
                        resendSuccess.value = false;
                    }, 5000);

                } catch (error) {
                    alert('Ошибка при отправке письма: ' + (error.response?.data?.message || 'Попробуйте позже'));
                } finally {
                    resendLoading.value = false;
                }
            }

        // Загружаем данные сразу при запуске
        onMounted(() => {
            const urlParams = new URLSearchParams(window.location.search);
            const error = urlParams.get('error');
            const success = urlParams.get('success');

            if (error) {
                Swal.fire({
                    icon: 'error',
                    title: 'Ошибка подтверждения',
                    text: decodeURIComponent(error),
                });
            } else if (success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Успешно!',
                    text: 'Ваша почта подтверждена.',
                });
            }

            setInterval(() => {
                if (selectedAirport.value?.time_zone) {
                    localTime.value = formatLocalTime(selectedAirport.value.time_zone);
                }
            }, 1000);
            getUserLocation();
            fetchAirports(1);
        });

        return {
            showAuthModal,
            showDetailsModal,
            isLoginForm,
            selectedAirport,
            nearestdAirport,
            nearestAirportsCity,
            nearestAirportsLoading,
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
            currentPage,
            totalPages,
            localTime,
            citySearch,
            filteredCities,
            resendLoading,
            resendSuccess,
            openCityModal,
            selectCity,
            selectFirstCity,
            formatLocalTime,
            prevPage,
            nextPage,
            openUserModal,
            showAirportDetails,
            login,
            register,
            logout,
            fetchAirports,
            resendVerificationEmail
        };
    }
}).mount('#app');
