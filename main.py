import selenium.webdriver.common.bidi.cdp
from selenium import webdriver


from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
import sqlite3

from selenium.webdriver.support.wait import WebDriverWait, TimeoutException

from selenium.webdriver.support import expected_conditions as EC

firefox_binary_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"
firefox_options = Options()
# firefox_options.add_argument("--headless")
firefox_options.binary_location = firefox_binary_path


# Параметры для увеличения схожести с обычным пользователем
firefox_options.add_argument(f"--window-size=1440,1080")
firefox_options.add_argument("--disable-blink-features=AutomationControlled")  # Отключаем автоматизацию
firefox_options.add_argument('--disable-gpu')  # Отключаем GPU
firefox_options.add_argument('--disable-browser-side-navigation')  # Отключаем навигацию
firefox_options.add_argument('--no-sandbox')  # Запуск без песочницы
firefox_options.add_argument('--disable-dev-shm-usage')  # Отключаем shared memory
firefox_options.add_argument('--incognito')  # Запуск в режиме инкогнито

# Дополнительные трюки для сокрытия Selenium
firefox_options.set_preference("dom.webdriver.enabled", False)  # Отключение webdriver-флага
firefox_options.set_preference("useAutomationExtension", False)  # Отключение расширений автоматизации
firefox_options.set_preference("media.navigator.enabled", False)  # Отключаем запросы на использование камеры/микрофона
firefox_options.set_preference("general.platform.override", "Win64")  # Подделка операционной системы
firefox_options.set_preference("network.http.sendRefererHeader", 0)  # Отключаем отправку заголовков Referer


gecko_driver_path = r"E:\Path\to\geckodriver.exe"
service = Service(executable_path=gecko_driver_path)

# Запуск браузера
driver = webdriver.Firefox(service=service, options=firefox_options)

critical_error_counter = 0

# Открываем страницу
driver.get('https://getgems.io/user/UQAKQT6VMOmsPHIV-DeJrU_IvOHx1uxuNdqfvoVxRsmwk_um')



# Путь к файлу с именами кошельков
wallet_file = 'data/wallet.txt'

# Устанавливаем соединение с базой данных SQLite
conns = sqlite3.connect('data/wallets.db')
cursors = conns.cursor()

# Создаем таблицу для хранения данных по кошелькам, если она еще не существует
cursors.execute('''
CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_name TEXT UNIQUE,
    page_content TEXT
)
''')
conns.commit()


# Функция для загрузки страницы и обработки данных
def process_wallet(wallet_name):
    url = f'https://getgems.io/user/{wallet_name}'

    # Открываем страницу
    driver.get(url)

    # Ожидаем, пока страница загрузится
    driver.implicitly_wait(10)

    # Получаем HTML-контент страницы
    html = driver.page_source
    cnt = 0
    time.sleep(0.1)
    while True:
        if 'You have no NFTs' in html:
            # Записываем данные в базу данных SQLite
            try:
                cursors.execute("INSERT INTO wallets (wallet_name, page_content) VALUES (?, ?)",
                                (wallet_name, 'Not NFT'))
                conns.commit()
            except sqlite3.IntegrityError:
                pass

            # Место для дальнейшей обработки HTML-контента
            print(f"Данные для кошелька {wallet_name} успешно записаны.")
            break
        else:
            try:
                # Явное ожидание загрузки контейнера
                try:
                    container = WebDriverWait(driver, 0.1).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "EntityContentContainer"))
                    )
                except TimeoutException:
                    print(f"Не удалось загрузить контейнер для кошелька {wallet_name}.")
                    return

                # Проверяем, пустой ли контейнер
                grid_items = container.find_elements(By.CLASS_NAME, "NftItemContainer")

                visible_items = [item for item in grid_items if item.is_displayed()]  # Только видимые элементы

                if len(visible_items) > 0:
                    # print(f"Контейнер не пустой, найдено {len(visible_items)} видимых элементов")
                    if len(visible_items) == 30:
                        print('continue. . .')
                        time.sleep(5)
                        continue
                    print(visible_items)
                    # Дополнительно можно обрабатывать найденные элементы
                    for item in visible_items:
                        if item.text.strip():
                            # Пример: получаем текст элемента
                            print(item.text)
                else:
                    print("Контейнер пустой")
            except NoSuchElementException:
                print("Контейнер не найден")
                break

            try:
                # Записываем данные в базу данных SQLite
                cursors.execute("INSERT INTO wallets (wallet_name, page_content) VALUES (?, ?)",
                                (wallet_name, '+++ NFT'))
                conns.commit()

                # Место для дальнейшей обработки HTML-контента
                print(f"Данные для кошелька {wallet_name} успешно записаны.")
                break
            except sqlite3.IntegrityError:
                break
                pass


# Читаем файл с именами кошельков и обрабатываем каждую строку
with open(wallet_file, 'r') as file:
    for line in file:
        wallet_name = line.strip()
        if wallet_name:  # Проверяем, что строка не пустая
            process_wallet(wallet_name)

# Закрываем браузер и соединение с базой данных
driver.quit()
conns.close()

