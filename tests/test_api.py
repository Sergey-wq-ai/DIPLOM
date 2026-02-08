"""Модуль для тестирования API Кинопоиска."""
import os
import sys
from typing import Generator, Any

import allure
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()


API_KEY = os.getenv('KINOPOISK_API_KEY')


@pytest.fixture(scope='session')
def api_client() -> Generator[requests.Session, Any, None]:
    """Фикстура для API клиента с правильными заголовками."""
    session = requests.Session()
    session.headers.update({
        "X-API-KEY": API_KEY,
        "accept": "application/json"
    })
    session.timeout = 10
    yield session
    session.close()


@allure.feature("API Tests")
class TestKinopoiskAPI:
    """Класс с тестами для API Кинопоиска."""
    
    @allure.title("Проверка валидности API ключа")
    @allure.description("Тест проверяет, что API ключ действителен и можно получить данные")
    @allure.story("Authentication")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_api_key_valid(self, api_client: requests.Session) -> None:
        """Тест проверки валидности API ключа."""
        with allure.step("Отправка запроса для проверки API ключа"):
            response = api_client.get(
                "https://api.kinopoisk.dev/v1.4/movie",
                params={"limit": 1}
            )

        allure.attach(
            f"Status Code: {response.status_code}",
            name="Response Status",
            attachment_type=allure.attachment_type.TEXT
        )

        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📋 Response preview: {response.text[:200]}...")

        with allure.step("Проверка статус кода и структуры ответа"):
            assert response.status_code == 200, f"API вернул статус {response.status_code}"
            assert "docs" in response.json(), "Ответ не содержит ключ 'docs'"

        print("✅ API ключ валиден!")
        allure.attach(
            "✅ API ключ валиден!",
            name="Result",
            attachment_type=allure.attachment_type.TEXT
        )

    @allure.title("Поиск фильма 'Шрек'")
    @allure.description("Тест проверяет поиск фильма по названию")
    @allure.story("Search")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_api_search_shrek(self, api_client: requests.Session) -> None:
        """Тест поиска Шрека через API."""
        with allure.step("Выполнение поиска 'Шрек'"):
            print("\n🔍 Ищем фильм 'Шрек'...")
            response = api_client.get(
                "https://api.kinopoisk.dev/v1.4/movie/search",
                params={"query": "Шрек", "limit": 3}
            )

        print(f"📊 Status: {response.status_code}")

        with allure.step("Проверка успешности запроса"):
            assert response.status_code == 200, f"Ошибка поиска: {response.status_code}"

        data = response.json()
        movies = data.get('docs', [])

        with allure.step("Проверка наличия результатов поиска"):
            assert len(movies) > 0, "Фильм 'Шрек' не найден"

        found = False
        for movie in movies:
            if "шрек" in movie.get('name', '').lower():
                found = True
                print(f"✅ Найден: {movie['name']} ({movie.get('year', 'N/A')})")
                break

        with allure.step("Проверка корректности найденного фильма"):
            assert found, "Не найден фильм 'Шрек' в результатах"

    @allure.title("Поиск фильмов с возрастным рейтингом 16+")
    @allure.description("Тест проверяет поиск фильмов с рейтингом 16+")
    @allure.story("Filtering")
    @pytest.mark.api
    def test_api_movies_16_plus(self, api_client: requests.Session) -> None:
        """Тест фильмов с возрастным рейтингом 16+ через API."""
        with allure.step("Поиск фильмов с рейтингом 16+"):
            print("\n🔞 Ищем фильмы с возрастным рейтингом 16+...")
            response = api_client.get(
                "https://api.kinopoisk.dev/v1.4/movie",
                params={
                    "ageRating": "16",
                    "limit": 5,
                    "sortField": "rating.kp",
                    "sortType": "-1"
                }
            )

        with allure.step("Проверка успешности запроса"):
            assert response.status_code == 200

        data = response.json()
        movies = data.get('docs', [])

        with allure.step("Проверка наличия результатов"):
            assert len(movies) > 0, "Не найдено фильмов с рейтингом 16+"

        movie_list = []
        for movie in movies:
            age_rating = movie.get('ageRating', 0)
            movie_list.append(f"{movie.get('name')}: рейтинг {age_rating}+")
            
            with allure.step(f"Проверка возрастного рейтинга {movie.get('name')}"):
                try:
                    rating_value = int(str(age_rating).replace('+', '').strip())
                    assert rating_value >= 16, f"Фильм {movie.get('name')} имеет рейтинг {age_rating} < 16"
                except (ValueError, TypeError):
                    print(f"⚠ Не удалось преобразовать рейтинг: {age_rating}")

        allure.attach(
            "\n".join(movie_list),
            name="Movies with age rating 16+",
            attachment_type=allure.attachment_type.TEXT
        )
        print(f"✅ Найдено {len(movies)} фильмов с рейтингом 16+")

    @allure.title("Поиск фильмов по году")
    @allure.description("Тест проверяет поиск фильмов 2001 года (год выхода Шрека)")
    @allure.story("Filtering")
    @pytest.mark.api
    def test_api_movies_by_year(self, api_client: requests.Session) -> None:
        """Тест фильмов по году через API."""
        with allure.step("Поиск фильмов 2001 года"):
            print("\n📅 Ищем фильмы 2001 года...")
            response = api_client.get(
                "https://api.kinopoisk.dev/v1.4/movie",
                params={"year": "2001", "limit": 5}
            )

        with allure.step("Проверка успешности запроса"):
            assert response.status_code == 200

        data = response.json()
        movies = data.get('docs', [])

        with allure.step("Проверка наличия результатов"):
            assert len(movies) > 0, "Не найдено фильмов 2001 года"

        movie_list = []
        for movie in movies:
            movie_list.append(f"{movie.get('name')} ({movie.get('year')})")
            with allure.step(f"Проверка года выпуска {movie.get('name')}"):
                assert movie.get('year') == 2001, f"Фильм {movie.get('name')} не 2001 года"

        allure.attach(
            "\n".join(movie_list),
            name="Movies from 2001",
            attachment_type=allure.attachment_type.TEXT
        )
        print(f"✅ Найдено {len(movies)} фильмов 2001 года")

    @allure.title("Поиск фильмов по жанру 'мультфильм'")
    @allure.description("Тест проверяет поиск фильмов по жанру")
    @allure.story("Filtering")
    @pytest.mark.api
    def test_api_movies_by_genre(self, api_client: requests.Session) -> None:
        """Тест поиска фильмов по жанру."""
        with allure.step("Поиск фильмов по жанру 'мультфильм'"):
            print("\n🎭 Ищем фильмы в жанре 'мультфильм'...")
            response = api_client.get(
                "https://api.kinopoisk.dev/v1.4/movie",
                params={
                    "genres.name": "мультфильм",
                    "limit": 5,
                    "sortField": "rating.kp",
                    "sortType": "-1"
                }
            )

        with allure.step("Проверка успешности запроса"):
            assert response.status_code == 200, f"Ошибка при поиске по жанру: {response.status_code}"

        data = response.json()
        movies = data.get('docs', [])

        with allure.step("Проверка наличия результатов"):
            assert len(movies) > 0, "Не найдено фильмов в жанре 'мультфильм'"

        movie_list = []
        for movie in movies:
            genres = movie.get('genres', [])
            genre_names = [genre.get('name', '').lower() for genre in genres]
            
            movie_list.append(f"{movie.get('name')} - жанры: {', '.join(genre_names)}")
            
            with allure.step(f"Проверка жанров фильма {movie.get('name')}"):
                is_animation = any(
                    any(keyword in name for keyword in ['мультфильм', 'анимация', 'animation'])
                    for name in genre_names
                )
                assert is_animation, f"Фильм {movie.get('name')} не относится к жанру 'мультфильм'"

        allure.attach(
            "\n".join(movie_list),
            name="Animation movies",
            attachment_type=allure.attachment_type.TEXT
        )
        print(f"✅ Найдено {len(movies)} мультфильмов")

    @allure.title("Проверка поиска сериалов")
    @allure.description("Простой тест для поиска популярных сериалов")
    @allure.story("Search")
    @pytest.mark.api
    def test_api_search_series(self, api_client: requests.Session) -> None:
        """Тест поиска сериалов."""
        with allure.step("Поиск популярных сериалов"):
            print("\n📺 Ищем популярные сериалы...")
            response = api_client.get(
                "https://api.kinopoisk.dev/v1.4/movie",
                params={
                    "type": "tv-series",
                    "limit": 3,
                    "sortField": "rating.kp",
                    "sortType": "-1"
                }
            )

        with allure.step("Проверка успешности запроса"):
            assert response.status_code == 200, f"Ошибка при поиске сериалов: {response.status_code}"
        
        data = response.json()
        series = data.get('docs', [])
        
        with allure.step("Проверка наличия результатов"):
            assert len(series) > 0, "Не найдено сериалов"
        
        series_list = []
        for series_item in series:
            series_name = series_item.get('name', 'Без названия')
            series_year = series_item.get('year', 'Н/Д')
            series_rating = series_item.get('rating', {}).get('kp', 'Н/Д')
            
            series_list.append(f"{series_name} ({series_year}) - рейтинг: {series_rating}")
            print(f"📺 Найден сериал: {series_name} ({series_year}) - рейтинг: {series_rating}")
        
        allure.attach(
            "\n".join(series_list),
            name="Found series",
            attachment_type=allure.attachment_type.TEXT
        )
        print(f"✅ Найдено {len(series)} сериалов")


if __name__ == "__main__":
    print("🚀 Запуск тестов API Кинопоиска...")
    print("=" * 50)
    
    exit_code = pytest.main([
        '-v',
        '-s',
        '--tb=short',
        '--disable-warnings',
        '--alluredir=allure-results',
        __file__
    ])
    
    print("=" * 50)
    print("🏁 Тестирование завершено!")
    sys.exit(exit_code)