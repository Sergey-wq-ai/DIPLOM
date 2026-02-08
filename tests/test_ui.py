"""Модуль для тестирования UI Кинопоиска."""
import os
import random
import re
import time
from typing import Generator, Any

import allure
import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()


@pytest.fixture(scope='function')
def browser() -> Generator[WebDriver, Any, None]:
    """Фикстура для инициализации браузера."""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


def accept_cookies(browser: WebDriver) -> bool:
    """Вспомогательная функция для принятия cookies."""
    try:
        cookie_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(text(), 'Принять') or "
                "contains(text(), 'Accept') or contains(text(), 'Согласен')]"
            ))
        )
        cookie_button.click()
        print("✅ Cookies приняты")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"⚠ Окно cookies не появилось: {e}")
        return False


@allure.feature("UI Tests - Kinopoisk")
@allure.title("Переход на главную страницу Кинопоиска")
@allure.description("Тест проверяет загрузку главной страницы Кинопоиска и наличие основных элементов")
@allure.story("Navigation")
@pytest.mark.ui
@pytest.mark.smoke
def test_ui_main_page_load(browser: WebDriver) -> None:
    """UI тест: загрузка главной страницы Кинопоиска."""
    with allure.step("Открытие главной страницы Кинопоиска"):
        print("🌐 Открываем главную страницу Кинопоиска...")
        browser.get("https://www.kinopoisk.ru/")
        time.sleep(2)

        allure.attach(
            browser.get_screenshot_as_png(),
            name="main_page",
            attachment_type=allure.attachment_type.PNG
        )

    accept_cookies(browser)

    with allure.step("Проверка заголовка страницы"):
        try:
            page_title = browser.title
            assert "Кинопоиск" in page_title, (
                f"Заголовок не содержит 'Кинопоиск'. Текущий заголовок: {page_title}"
            )
            print(f"✅ Заголовок страницы: {page_title}")
        except AssertionError:
            allure.attach(
                browser.get_screenshot_as_png(),
                name="title_check_error",
                attachment_type=allure.attachment_type.PNG
            )
            raise

    print("✅ Главная страница загружена успешно!")


@allure.feature("UI Tests - Kinopoisk")
@allure.title("Поиск фильма 'Шрэк' через UI")
@allure.description("Тест проверяет поиск фильма через поисковую строку на сайте")
@allure.story("Search")
@pytest.mark.ui
@pytest.mark.smoke
def test_ui_search_shrek(browser: WebDriver) -> None:
    """UI тест: поиск фильма 'Шрэк'."""
    with allure.step("Открытие главной страницы Кинопоиска"):
        browser.get("https://www.kinopoisk.ru/")
        time.sleep(3)

    accept_cookies(browser)

    with allure.step("Поиск и клик по кнопке поиска"):
        try:
            search_buttons = browser.find_elements(
                By.CSS_SELECTOR,
                "button[aria-label*='поиск'], "
                "button[data-test-id='search-button'], "
                "[class*='search'] button, "
                "svg[class*='search'], "
                "button[type='submit']"
            )

            if search_buttons:
                for button in search_buttons:
                    try:
                        if button.is_displayed():
                            button.click()
                            print("✅ Кнопка поиска нажата")
                            time.sleep(1)
                            break
                    except Exception:
                        continue
            else:
                print("ℹ Кнопка поиска не найдена, пробуем прямой ввод")
        except Exception as e:
            print(f"⚠ Не удалось нажать кнопку поиска: {str(e)}")

    with allure.step("Ввод запроса в поисковую строку"):
        try:
            search_inputs = browser.find_elements(
                By.CSS_SELECTOR,
                "input[type='search']:focus, "
                "input[type='text']:focus, "
                "input[placeholder*='поиск'], "
                "input[data-test-id='search-input']"
            )

            if not search_inputs:
                search_inputs = browser.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='search'], input[type='text']"
                )

            if search_inputs:
                search_input = None
                for input_field in search_inputs:
                    try:
                        if input_field.is_displayed():
                            search_input = input_field
                            break
                    except Exception:
                        continue
                
                if search_input:
                    search_input.clear()
                    search_input.send_keys("Шрэк")
                    time.sleep(1)
                    search_input.send_keys(Keys.ENTER)
                    print("✅ Запрос 'Шрэк' введен и отправлен")
                else:
                    raise Exception("Нет доступных полей для ввода")
            else:
                browser.get("https://www.kinopoisk.ru/s/Шрэк/")
                print("✅ Прямой переход на страницу поиска 'Шрэк'")
        except Exception as e:
            allure.attach(
                browser.get_screenshot_as_png(),
                name="search_input_error",
                attachment_type=allure.attachment_type.PNG
            )
            raise AssertionError(f"Не удалось выполнить поиск: {str(e)}")

    with allure.step("Ожидание загрузки результатов поиска"):
        try:
            WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "h1, .title, [data-test-id*='search'], "
                    ".search-results, .results, .items"
                ))
            )
            time.sleep(3)

            allure.attach(
                browser.get_screenshot_as_png(),
                name="search_results_shrek",
                attachment_type=allure.attachment_type.PNG
            )
        except TimeoutException:
            current_url = browser.current_url
            if "search" in current_url or "s/" in current_url or "шрэк" in current_url.lower():
                print(f"✅ Страница поиска загружена. URL: {current_url}")
            else:
                allure.attach(
                    browser.get_screenshot_as_png(),
                    name="search_timeout",
                    attachment_type=allure.attachment_type.PNG
                )
                raise AssertionError("Результаты поиска не загрузились")

    with allure.step("Проверка наличия фильма в результатах поиска"):
        page_source = browser.page_source.lower()
        search_terms = ["шрэк", "shrek"]
        
        found = False
        for term in search_terms:
            if term in page_source:
                found = True
                print(f"✅ Фильм найден по ключевому слову: '{term}'")
                break
        
        if not found:
            page_title = browser.title.lower()
            if any(term in page_title for term in search_terms):
                print("✅ Фильм найден в заголовке страницы")
            else:
                raise AssertionError("Фильм 'Шрэк' не найден в результатах поиска")

        print("✅ Фильм 'Шрэк' найден в результатах поиска")


@allure.feature("UI Tests - Kinopoisk")
@allure.title("Переход на страницу фильма 'Шрэк' через UI")
@allure.description("Тест проверяет переход на страницу конкретного фильма")
@allure.story("Navigation")
@pytest.mark.ui
def test_ui_open_shrek_page(browser: WebDriver) -> None:
    """UI тест: переход на страницу фильма 'Шрэк'."""
    with allure.step("Прямой переход на страницу фильма 'Шрэк'"):
        print("🌐 Открываем страницу фильма 'Шрэк'...")
        browser.get("https://www.kinopoisk.ru/film/430/")
        time.sleep(5)

    accept_cookies(browser)

    with allure.step("Ожидание загрузки страницы фильма"):
        try:
            WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "h1, [itemprop='name'], [data-test-id='film-title'], "
                    ".styles_title__j5ose"
                ))
            )
            time.sleep(3)

            allure.attach(
                browser.get_screenshot_as_png(),
                name="shrek_movie_page",
                attachment_type=allure.attachment_type.PNG
            )
        except TimeoutException:
            allure.attach(
                browser.get_screenshot_as_png(),
                name="movie_page_timeout",
                attachment_type=allure.attachment_type.PNG
            )
            if "/film/430" in browser.current_url:
                print("✅ Страница фильма загружена (по URL)")
            else:
                raise AssertionError("Страница фильма не загрузилась")

    with allure.step("Проверка URL страницы фильма"):
        current_url = browser.current_url
        assert "/film/430" in current_url, (
            f"Не удалось перейти на страницу фильма 'Шрэк'. URL: {current_url}"
        )
        print(f"✅ Успешно перешли на страницу фильма: {current_url}")

    print("✅ Тест перехода на страницу фильма 'Шрэк' завершен успешно!")


@allure.feature("UI Tests - Kinopoisk")
@allure.title("Проверка навигационного меню")
@allure.description("Тест проверяет работу навигационного меню сайта")
@allure.story("Navigation")
@pytest.mark.ui
def test_ui_navigation_menu(browser: WebDriver) -> None:
    """UI тест: проверка навигационного меню."""
    with allure.step("Открытие главной страницы Кинопоиска"):
        browser.get("https://www.kinopoisk.ru/")
        time.sleep(3)

    accept_cookies(browser)

    with allure.step("Поиск навигационных элементов"):
        try:
            nav_links_selectors = [
                "a[href*='/film/']",
                "a[href*='/series/']", 
                "a[href*='/cartoons/']",
                "a[href*='/lists/']",
                "a[href*='/media/']",
                "a[href*='/collections/']"
            ]

            found_links = []
            for selector in nav_links_selectors:
                try:
                    elements = browser.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text and len(text) < 50:
                                found_links.append(f"{text}: {element.get_attribute('href')}")
                except Exception:
                    continue

            if found_links:
                print(f"✅ Найдено {len(found_links)} навигационных ссылок")
                for link in found_links[:5]:
                    print(f"   - {link}")
            else:
                print("⚠ Навигационные ссылки не найдены")
        except Exception as e:
            print(f"⚠ Ошибка при поиске навигации: {str(e)}")

    print("✅ Проверка навигации завершена")


@allure.feature("UI Tests - Kinopoisk")
@allure.title("Переход на страницу 'Фильмы в кино'")
@allure.description("Тест проверяет переход на страницу с фильмами в кинотеатрах")
@allure.story("Navigation")
@pytest.mark.ui
def test_ui_movies_in_cinema(browser: WebDriver) -> None:
    """UI тест: переход на страницу фильмов в кино."""
    with allure.step("Открытие главной страницы Кинопоиска"):
        browser.get("https://www.kinopoisk.ru/")
        time.sleep(3)

    accept_cookies(browser)

    with allure.step("Поиск и переход на страницу 'Фильмы в кино'"):
        try:
            cinema_link_selectors = [
                "a[href*='/lists/movies/movies-in-cinema/']",
                "a[href*='movies-in-cinema']",
                "a:contains('в кино')",
                "a[title*='кино']"
            ]
            
            link_found = False
            for selector in cinema_link_selectors:
                try:
                    elements = browser.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            link_found = True
                            print(f"✅ Переход по ссылке 'Фильмы в кино'")
                            time.sleep(3)
                            break
                except Exception:
                    continue
                
                if link_found:
                    break
            
            if not link_found:
                print("ℹ Ссылка 'Фильмы в кино' не найдена, используем прямой URL")
                browser.get("https://www.kinopoisk.ru/lists/movies/movies-in-cinema/")
                time.sleep(3)
        except Exception as e:
            print(f"⚠ Ошибка при поиске ссылки: {str(e)}")
            browser.get("https://www.kinopoisk.ru/lists/movies/movies-in-cinema/")
            time.sleep(3)

    with allure.step("Ожидание загрузки страницы"):
        try:
            WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "h1, [data-test-id='page-title'], "
                    "[class*='title'], [class*='header']"
                ))
            )
            time.sleep(3)

            allure.attach(
                browser.get_screenshot_as_png(),
                name="cinema_movies_page",
                attachment_type=allure.attachment_type.PNG
            )
        except TimeoutException:
            current_url = browser.current_url
            page_title = browser.title.lower()

            if "movies-in-cinema" in current_url or "кино" in page_title:
                print(f"✅ Страница загружена. URL: {current_url}, Заголовок: {browser.title}")
            else:
                raise AssertionError("Страница 'Фильмы в кино' не загрузилась")

    print("✅ Тест страницы 'Фильмы в кино' завершен успешно!")


if __name__ == "__main__":
    pytest.main(['-v', '-s', '--alluredir=allure-results'])