import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chrome配置
CHROME_OPTIONS = {
    'arguments': [
        '--disable-gpu',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--window-size=1920,1080',
        '--start-maximized',
        '--disable-extensions',
        '--disable-popup-blocking',
        '--disable-blink-features=AutomationControlled',
        '--lang=zh-CN'
    ]
}

# 爬虫配置
SCRAPER_CONFIG = {
    'MAX_RETRIES': 3,
    'WAIT_TIMEOUT': 10,
    'SCROLL_PAUSE_TIME': 5,
    'PAGE_LOAD_TIMEOUT': 30
}

# 输出配置
OUTPUT_DIR = os.path.join(BASE_DIR, 'output') 