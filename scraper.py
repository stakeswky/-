import time
import re
import os
import sys
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class GoogleMapsScraper:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.is_paused = False
        self.total_results = []
        self.current_query = None

    def initialize(self, log_callback=None):
        try:
            if log_callback:
                log_callback("正在初始化Chrome浏览器...")
            
            chrome_options = Options()
            # 配置无头模式
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # 设置窗口大小和用户代理
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--hide-scrollbars')
            chrome_options.add_argument('--enable-javascript')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # 添加用户代理
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 添加其他性能优化选项
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--lang=zh-CN')
            chrome_options.add_argument('--remote-debugging-port=9222')
            
            # 添加实验性选项
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 修改 ChromeDriver 路径检测逻辑
            if sys.platform == 'win32':
                chromedriver_name = 'chromedriver.exe'
            else:
                chromedriver_name = 'chromedriver'
            
            chromedriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), chromedriver_name)
            
            if not os.path.exists(chromedriver_path):
                if log_callback:
                    log_callback(f"警告：未在 {chromedriver_path} 找到 ChromeDriver")
                    log_callback("尝试使用系统 PATH 中的 ChromeDriver")
                chromedriver_path = None  # 让 Selenium 自动在 PATH 中查找
            
            if log_callback:
                log_callback(f"使用ChromeDriver: {chromedriver_path}")
            
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # 执行一些初始化JavaScript
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            if log_callback:
                log_callback("Chrome浏览器初始化成功")
            return True
        except Exception as e:
            if log_callback:
                log_callback(f"初始化错误: {str(e)}")
            return False

    def close(self, log_callback=None):
        try:
            if self.driver:
                if log_callback:
                    log_callback("正在关闭浏览器...")
                self.driver.quit()
                self.driver = None
                if log_callback:
                    log_callback("浏览器已关闭")
        except Exception as e:
            if log_callback:
                log_callback(f"关闭错误: {str(e)}")

    def create_search_query(self, business_type, country):
        return f"{business_type} in {country}"

    def search_places(self, query, log_callback=None):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if log_callback:
                    log_callback(f"尝试第 {retry_count + 1} 次搜索...")
                
                # 打开Google Maps
                self.driver.get("https://www.google.com/maps")
                time.sleep(3)  # 等待页面加载
                
                # 等待搜索框出现
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input#searchboxinput"))
                )
                
                # 清除搜索框内容并输入搜索词
                search_box.clear()
                for char in query:
                    search_box.send_keys(char)
                    time.sleep(0.1)  # 模拟人工输入
                time.sleep(1)
                
                # 点击搜索按钮
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button#searchbox-searchbutton"))
                )
                search_button.click()
                
                # 等待搜索结果加载
                try:
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf'))
                    )
                    
                    # 等待一段时间，确保结果完全加载
                    time.sleep(3)
                    
                    # 检查是否有结果
                    results = self.driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
                    if not results:
                        results = self.driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK.THOPZb.CpccDe')
                    
                    if not results:
                        if log_callback:
                            log_callback("未找到搜索结果，尝试重试...")
                        retry_count += 1
                        continue
                    
                    return True
                    
                except TimeoutException:
                    if log_callback:
                        log_callback("等待搜索结果超时")
                    retry_count += 1
                    continue
                    
            except Exception as e:
                retry_count += 1
                if log_callback:
                    log_callback(f"搜索失败 ({retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(5)  # 增加等待时间
                else:
                    return False
        
        return False

    def scroll_results(self, log_callback=None):
        try:
            # 滚动结果列表以加载更多内容
            try:
                scrollable_section = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf'))
                )
            except TimeoutException:
                if log_callback:
                    log_callback("错误：未找到可滚动的结果列表")
                return
                
            if scrollable_section:
                if log_callback:
                    log_callback("正在滚动加载更多结果...")
                prev_height = 0
                for i in range(3):  # 限制滚动次数
                    try:
                        curr_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable_section)
                        if curr_height == prev_height:
                            if log_callback:
                                log_callback("已到达列表底部")
                            break
                        self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", scrollable_section)
                        time.sleep(5)  # 增加等待时间
                        prev_height = curr_height
                        if log_callback:
                            log_callback(f"已完成第 {i+1} 次滚动，高度: {curr_height}")
                    except Exception as e:
                        if log_callback:
                            log_callback(f"滚动操作失败: {str(e)}")
                        break
        except Exception as e:
            if log_callback:
                log_callback(f"滚动错误: {str(e)}")

    def scrape(self, business_type, country, target_count, progress_callback=None, log_callback=None):
        try:
            self.is_running = True
            self.total_results = []
            self.current_query = f"{business_type} in {country}"
            
            # 初始化浏览器
            if not self.initialize(log_callback):
                if log_callback:
                    log_callback("浏览器初始化失败")
                return
            
            if log_callback:
                log_callback(f"开始搜索: {self.current_query}")
                log_callback(f"目标获取商户数量: {target_count}")

            if not self.search_places(self.current_query, log_callback):
                if log_callback:
                    log_callback("搜索失败")
                return

            processed_names = set()  # 用于跟踪已处理的商家名称
            
            while len(self.total_results) < target_count and self.is_running:
                if self.is_paused:
                    time.sleep(1)
                    continue

                try:
                    # 等待搜索结果列表加载
                    wait = WebDriverWait(self.driver, 10)
                    results_container = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf'))
                    )
                    
                    # 获取当前可见的所有商家元素
                    elements = results_container.find_elements(By.CSS_SELECTOR, 'div.Nv2PK.THOPZb.CpccDe')
                    if not elements:  # 如果找不到，尝试其他选择器
                        elements = results_container.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
                    
                    if log_callback:
                        log_callback(f"当前页面找到 {len(elements)} 个商户")
                    
                    for element in elements:
                        if not self.is_running or len(self.total_results) >= target_count:
                            break
                            
                        if self.is_paused:
                            continue
                        
                        try:
                            # 获取商家信息
                            result = self.extract_place_info(element, log_callback)
                            if result and result['name'] not in processed_names:
                                self.total_results.append(result)
                                processed_names.add(result['name'])
                                
                                if progress_callback:
                                    progress_callback(int(len(self.total_results) / target_count * 100))
                            
                        except Exception as e:
                            if log_callback:
                                log_callback(f"处理商户时出错: {str(e)}")
                            continue
                    
                    # 如果还需要更多结果，滚动加载
                    if len(self.total_results) < target_count:
                        last_height = self.driver.execute_script("return arguments[0].scrollHeight", results_container)
                        self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", results_container)
                        time.sleep(2)
                        
                        new_height = self.driver.execute_script("return arguments[0].scrollHeight", results_container)
                        if new_height == last_height:
                            # 尝试点击"加载更多"按钮（如果存在）
                            try:
                                load_more = self.driver.find_element(By.CSS_SELECTOR, "button.HlvSq")
                                if load_more.is_displayed():
                                    load_more.click()
                                    time.sleep(2)
                                else:
                                    break  # 没有更多结果了
                            except:
                                break  # 没有更多结果了
                    
                except Exception as e:
                    if log_callback:
                        log_callback(f"获取商户列表失败: {str(e)}")
                    # 尝试恢复搜索结果页面
                    try:
                        self.driver.refresh()
                        time.sleep(2)
                        self.search_places(self.current_query, log_callback)
                    except:
                        break

            # 保存结果
            if self.total_results:
                try:
                    df = pd.DataFrame(self.total_results)
                    # 确保output目录存在
                    output_dir = "output"
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    # 在output目录下保存文件
                    filename = os.path.join(output_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{country}_{business_type}.csv")
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    if log_callback:
                        log_callback(f"数据已保存到文件: {filename}")
                except Exception as e:
                    if log_callback:
                        log_callback(f"保存数据时出错: {str(e)}")
            else:
                if log_callback:
                    log_callback("未获取到任何商户信息")

        except Exception as e:
            if log_callback:
                log_callback(f"爬虫运行错误: {str(e)}")
        finally:
            self.close(log_callback)
            self.is_running = False
            if progress_callback:
                progress_callback(100)
            if log_callback:
                log_callback("爬虫任务结束")

    def extract_place_info(self, element, log_callback=None):
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if log_callback:
                    log_callback("开始提取商户信息...")
                
                # 在点击前获取所有基本信息
                try:
                    name = element.find_element(By.CSS_SELECTOR, "div.qBF1Pd.fontHeadlineSmall").text.strip()
                    try:
                        rating = element.find_element(By.CSS_SELECTOR, "span.MW4etd").text.strip()
                    except:
                        rating = "N/A"
                except Exception as e:
                    if log_callback:
                        log_callback(f"获取基本信息失败: {str(e)}")
                    retry_count += 1
                    continue
                
                # 记录元素的位置信息并滚动
                try:
                    element_location = element.location
                    self.driver.execute_script("window.scrollTo(0, arguments[0]);", element_location['y'] - 100)
                    time.sleep(2)  # 增加等待时间
                except:
                    pass
                
                # 尝试多种方式点击商户详情
                clicked = False
                try:
                    # 重新获取元素（避免stale element）
                    elements = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.Nv2PK.THOPZb.CpccDe, div.Nv2PK'))
                    )
                    
                    # 查找匹配的元素
                    target_element = None
                    for elem in elements:
                        try:
                            current_name = elem.find_element(By.CSS_SELECTOR, "div.qBF1Pd.fontHeadlineSmall").text.strip()
                            if current_name == name:
                                target_element = elem
                                break
                        except:
                            continue
                    
                    if target_element:
                        # 确保元素在视图中
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_element)
                        time.sleep(1)
                        
                        # 方式1：使用JavaScript模拟点击
                        try:
                            self.driver.execute_script("""
                                arguments[0].click();
                                arguments[0].dispatchEvent(new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                }));
                            """, target_element)
                            clicked = True
                            time.sleep(2)  # 增加等待时间
                        except:
                            # 方式2：使用Actions链
                            try:
                                actions = webdriver.ActionChains(self.driver)
                                actions.move_to_element(target_element)
                                actions.click()
                                actions.perform()
                                clicked = True
                                time.sleep(2)
                            except:
                                # 方式3：点击名称元素
                                try:
                                    name_element = target_element.find_element(By.CSS_SELECTOR, "div.qBF1Pd.fontHeadlineSmall")
                                    self.driver.execute_script("arguments[0].click();", name_element)
                                    clicked = True
                                    time.sleep(2)
                                except:
                                    if log_callback:
                                        log_callback("所有点击方式都失败")
                except Exception as e:
                    if log_callback:
                        log_callback(f"点击过程出错: {str(e)}")
                
                if not clicked:
                    retry_count += 1
                    if log_callback:
                        log_callback("无法点击商户详情，尝试重试...")
                    continue
                
                # 等待详情页面加载
                time.sleep(3)  # 增加等待时间
                
                # 获取详细信息
                address = ""
                phone = ""
                
                try:
                    # 等待详情面板加载
                    details_panel = WebDriverWait(self.driver, 10).until(  # 增加等待时间
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.tLjsW.eKbjU"))
                    )
                    
                    # 点击所有展开按钮
                    expand_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                        "button.w8nwRe.kyuRq, button[aria-label*='展开'], button[aria-label*='更多']"
                    )
                    for button in expand_buttons:
                        if button.is_displayed() and button.is_enabled():
                            try:
                                self.driver.execute_script("arguments[0].click();", button)
                                time.sleep(1)  # 增加等待时间
                            except:
                                continue
                    
                    # 等待信息加载完成
                    time.sleep(2)
                    
                    # 获取所有可能包含信息的元素
                    info_elements = details_panel.find_elements(By.CSS_SELECTOR, 
                        "button.CsEnBe, div[role='button'], div.rogA2c, div.Io6YTe, div.kR99db, span.fontBodyMedium, div.cXHGnc"
                    )
                    
                    # 记录所有文本内容
                    all_texts = []
                    for elem in info_elements:
                        if elem.is_displayed():
                            try:
                                text = elem.text.strip()
                                if text:
                                    all_texts.append(text)
                                aria_label = elem.get_attribute("aria-label")
                                if aria_label:
                                    all_texts.append(aria_label)
                            except:
                                continue
                    
                    if log_callback:
                        log_callback(f"找到的所有文本: {all_texts}")
                    
                    # 从文本中识别地址和电话
                    for text in all_texts:
                        # 检查电话
                        if not phone:
                            # 尝试匹配电话号码模式
                            phone_matches = re.findall(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
                            if phone_matches:
                                phone = phone_matches[0]
                            # 如果文本中包含"电话"或"Phone"关键词
                            elif '电话' in text or 'Phone' in text:
                                # 提取数字和特殊字符
                                phone_text = re.sub(r'[^\d+\-() ]', '', text)
                                if phone_text:
                                    phone = phone_text
                        
                        # 检查地址
                        if not address:
                            # 如果文本包含地址相关关键词
                            if ('地址' in text or 'Address' in text or
                                any(char in text for char in [',', '路', '街', 'Road', 'Street', 'Ave', 'Boulevard', 'Lane'])):
                                # 如果文本长度合适且不是电话号码
                                if len(text) > 10 and not re.match(r'^[+\d\s-]+$', text):
                                    address = text.replace('地址：', '').replace('Address:', '').strip()
                    
                    # 如果还没找到，尝试从更大的容器中获取
                    if not (phone and address):
                        containers = details_panel.find_elements(By.CSS_SELECTOR, "div.RcCsl, div.Qe6Vdb, div.dbg0pd")
                        for container in containers:
                            try:
                                text = container.text.strip()
                                if text:
                                    lines = text.split('\n')
                                    for line in lines:
                                        if not phone:
                                            phone_matches = re.findall(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', line)
                                            if phone_matches:
                                                phone = phone_matches[0]
                                        if not address and len(line) > 10 and not re.match(r'^[+\d\s-]+$', line):
                                            if any(char in line for char in [',', '路', '街', 'Road', 'Street', 'Ave', 'Boulevard', 'Lane']):
                                                address = line
                            except:
                                continue
                    
                except Exception as e:
                    if log_callback:
                        log_callback(f"获取详细信息失败: {str(e)}")
                
                # 使用JavaScript关闭详情页面
                try:
                    self.driver.execute_script("""
                        var button = document.querySelector("button[aria-label='返回搜索结果']");
                        if (button) {
                            button.click();
                        } else {
                            document.dispatchEvent(new KeyboardEvent('keydown', {
                                key: 'Escape',
                                code: 'Escape',
                                keyCode: 27,
                                which: 27,
                                bubbles: true
                            }));
                        }
                    """)
                    time.sleep(2)  # 增加等待时间
                except:
                    webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(2)
                
                # 等待搜索结果列表可见
                try:
                    WebDriverWait(self.driver, 5).until(  # 增加等待时间
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf'))
                    )
                except:
                    pass
                
                if log_callback:
                    log_callback(f"获取到商户信息 - 名称: {name}, 地址: {address}, 电话: {phone}, 评分: {rating}")
                
                return {
                    "name": name,
                    "address": address,
                    "phone": phone,
                    "rating": rating
                }
                
            except Exception as e:
                retry_count += 1
                if log_callback:
                    log_callback(f"提取信息失败 ({retry_count}/{max_retries}): {str(e)}")
                
                if retry_count < max_retries:
                    time.sleep(2)  # 增加等待时间
                    try:
                        self.driver.execute_script("""
                            var button = document.querySelector("button[aria-label='返回搜索结果']");
                            if (button) {
                                button.click();
                            } else {
                                document.dispatchEvent(new KeyboardEvent('keydown', {
                                    key: 'Escape',
                                    code: 'Escape',
                                    keyCode: 27,
                                    which: 27,
                                    bubbles: true
                                }));
                            }
                        """)
                        time.sleep(2)
                    except:
                        webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(2)
                else:
                    return None 