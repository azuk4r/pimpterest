from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from os.path import join, exists, abspath, dirname, isfile
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from colorama import Fore, Style, init
from argparse import ArgumentParser
from os import makedirs, remove
from ffmpeg import input, Error
from selenium import webdriver
from datetime import datetime
from time import sleep, time
from requests import get
from re import compile
from json import loads
from uuid import uuid4
from tqdm import tqdm
from PIL import Image

init()

ascii_art = '''
   ▄███████▄  ▄█    ▄▄▄▄███▄▄▄▄      ▄███████▄     ███        ▄████████    ▄████████    ▄████████    ▄████████     ███     
  ███    ███ ███  ▄██▀▀▀███▀▀▀██▄   ███    ███ ▀█████████▄   ███    ███   ███    ███   ███    ███   ███    ███ ▀█████████▄ 
  ███    ███ ███▌ ███   ███   ███   ███    ███    ▀███▀▀██   ███    █▀    ███    ███   ███    █▀    ███    █▀     ▀███▀▀██ 
  ███    ███ ███▌ ███   ███   ███   ███    ███     ███   ▀  ▄███▄▄▄      ▄███▄▄▄▄██▀  ▄███▄▄▄       ███            ███   ▀ 
▀█████████▀  ███▌ ███   ███   ███ ▀█████████▀      ███     ▀▀███▀▀▀     ▀▀███▀▀▀▀▀   ▀▀███▀▀▀     ▀███████████     ███     
  ███        ███  ███   ███   ███   ███            ███       ███    █▄  ▀███████████   ███    █▄           ███     ███     
  ███        ███  ███   ███   ███   ███            ███       ███    ███   ███    ███   ███    ███    ▄█    ███     ███     
 ▄████▀      █▀    ▀█   ███   █▀   ▄████▀         ▄████▀     ██████████   ███    ███   ██████████  ▄████████▀     ▄████▀   
                                                                          ███    ███                                    
'''

print(f'\n{Fore.MAGENTA}{ascii_art}{Fore.RESET}')

def parse_args():
    parser = ArgumentParser(description='Pimpterest (Bcoz who needs permission to scrape the world?)')
    parser.add_argument('search_query', type=str, nargs='?', help='The keyword of your next Pinterest heist (search query)')
    parser.add_argument('total_elements', type=int, help='How deep do you wanna go? (total elements to scrape)')
    return parser.parse_args()

args = parse_args()
m3u8_url_pattern = compile(r'^https:\/\/v\d+\.pinimg\.com\/videos\/.*\.m3u8$')
total_elements = args.total_elements
driver_service = None

print(f'\n{Fore.MAGENTA}[pimpterest]{Style.RESET_ALL} [{datetime.now().strftime("%H:%M:%S")}] Pimpterest initialized! Scraping Pinterest for: "{args.search_query}". Let\'s burn this site!\n')

def download_driver():
    with tqdm(total=100, desc='Downloading ChromeDriver', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]') as pbar:
        for _ in range(99):
            sleep(0.05)
            pbar.update(1)
        service = Service(ChromeDriverManager().install())
        pbar.n = pbar.total
        pbar.refresh()
        pbar.close()
        return service

def get_timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def download_image(img_url, folder, name):
    if not img_url.startswith('http') or img_url.endswith('.svg'):
        return False
    img_data = get(img_url).content
    img_path = join(folder, name)
    with open(img_path, 'wb') as file:
        file.write(img_data)
    with Image.open(img_path) as image:
        if image.width == 60 and image.height == 60:
            image.close()
            remove(img_path)
            return False
    print(f'{Fore.MAGENTA}[pimpterest]{Style.RESET_ALL} [{datetime.now().strftime("%H:%M:%S")}] Successfully downloaded image: {name}. Pinterest can\'t stop us...')
    return True

def close_popup(driver):
    while True:
        try:
            popup = driver.find_element(By.CSS_SELECTOR, 'div.MIw.QLY.Rz6.hDW.p6V.zI7.iyn.Hsu')
            driver.execute_script('arguments[0].scrollIntoView(true);', popup)
            sleep(.1)
            popup.click()
            print(f'{Fore.MAGENTA}[pimpterest]{Style.RESET_ALL} [{datetime.now().strftime("%H:%M:%S")}] Annoying popup eliminated!')
        except NoSuchElementException:
            break
        except ElementClickInterceptedException:
            sleep(.1)

def scroll_down(driver):
    print(f'{Fore.MAGENTA}[pimpterest]{Style.RESET_ALL} [{datetime.now().strftime("%H:%M:%S")}] Scrolling down like a boss! Let\'s find more treasures!')
    driver.execute_script('window.scrollBy(0,100);')
    sleep(.5)

def process_element(element, driver, actions, output_folder):
    global processed_elements, last_mouseover_time
    if processed_elements >= total_elements:
        return
    try:
        src = element.get_attribute('poster') or element.get_attribute('src')
        if src and src not in visited_elements:
            visited_elements.add(src)
            if element.size['width'] > 60 and element.size['height'] > 60:
                driver.execute_script('arguments[0].scrollIntoView({block: "center"});', element)
                sleep(.1)
                actions.move_to_element(element).perform()
                sleep(.2)
                last_mouseover_time = time()
                unique_id = str(uuid4())
                image_name = f'IMG-{unique_id}.jpg'
                if download_image(src, output_folder, image_name):
                    content_data = {'id': processed_elements, 'image': image_name, 'video': None}
                    logs = driver.get_log('performance')
                    for log in logs:
                        if '.m3u8' in str(log):
                            log_json = loads(log['message'])
                            try:
                                m3u8_url = log_json['message']['params']['request']['url']
                                print(f'{Fore.MAGENTA}[pimpterest]{Style.RESET_ALL} [{datetime.now().strftime("%H:%M:%S")}] We got it! m3u8 URL: {m3u8_url}')
                                if '_audio.m3u8' not in m3u8_url and '_240w.m3u8' not in m3u8_url and '_360w.m3u8' not in m3u8_url:
                                    if m3u8_url_pattern.match(m3u8_url):
                                        video_name = f'VID-{unique_id}.mp4'
                                        content_data['video'] = (m3u8_url, video_name)
                            except KeyError:
                                print(f'{Fore.MAGENTA}[pimpterest]{Style.RESET_ALL} [{datetime.now().strftime("%H:%M:%S")}] Oops! KeyError while processing records. Let\'s keep rolling, nothing stops us!')
                                continue
                    contents.append(content_data)
                    processed_elements += 1
    except StaleElementReferenceException:
        scroll_down(driver)
    except Exception:
        close_popup(driver)
        scroll_down(driver)

def main():
    global driver_service, last_mouseover_time
    if not driver_service:
        driver_service = download_driver()
    keywords = []
    if args.search_query:
        keywords = [args.search_query]
    elif isfile('keywords.txt'):
        with open('keywords.txt', 'r') as file:
            keywords = [line.strip() for line in file if line.strip()]
    if not keywords:
        return
    for search_query in keywords:
        encoded_query = search_query.replace(' ', '%20')
        url = f'https://es.pinterest.com/search/pins/?q={encoded_query}&rs=typed'
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.add_argument('--lang=en')
        chrome_options.add_experimental_option('perfLoggingPrefs', {'enableNetwork': True, 'enablePage': False})
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        driver = webdriver.Chrome(service=driver_service, options=chrome_options)
        driver.get(url)
        sleep(3)
        actions = ActionChains(driver)
        global contents, visited_elements, processed_elements
        contents = []
        visited_elements = set()
        processed_elements = 0
        folder_name = search_query
        current_dir = dirname(abspath(__file__))
        output_folder = join(current_dir, folder_name)
        if not exists(output_folder):
            makedirs(output_folder)
        last_mouseover_time = time()
        while processed_elements < total_elements:
            current_time = time()
            if current_time - last_mouseover_time > 20:
                break
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, 'img.hCL.kVc.L4E.MIw, video.hwa.kVc.MIw.L4E')
                if not elements:
                    scroll_down(driver)
                else:
                    for element in elements:
                        process_element(element, driver, actions, output_folder)
                        if processed_elements >= total_elements:
                            break
            except Exception:
                close_popup(driver)
                scroll_down(driver)
        driver.quit()
        for content in contents:
            if content['video']:
                m3u8_url, video_name = content['video']
                video_path = join(output_folder, video_name)
                try:
                    input(m3u8_url).output(video_path, c='copy').run()
                except Error:
                    print(f'{Fore.RED}[ERROR]{Style.RESET_ALL} [{datetime.now().strftime("%H:%M:%S")}] Failed to download video: {m3u8_url}. Meh... not everything can be perfect.')

if __name__ == '__main__':
    main()
    print(f'{Fore.MAGENTA}[pimpterest]{Style.RESET_ALL} [{datetime.now().strftime("%H:%M:%S")}] Scraping completed. All treasures have been collected. Until next time.')
