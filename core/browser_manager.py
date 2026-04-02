
import os
import json
import time
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class BrowserType(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"
    SAFARI = "safari"


class AutomationEngine(Enum):
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"


@dataclass
class BrowserConfig:
    engine: str = "selenium"  # selenium or playwright
    browser_type: str = "chrome"
    headless: bool = False
    window_width: int = 1920
    window_height: int = 1080
    user_data_dir: str = ""
    proxy: str = ""
    user_agent: str = ""
    extensions: List[str] = field(default_factory=list)
    arguments: List[str] = field(default_factory=list)


@dataclass
class BrowserSession:
    session_id: str
    url: str
    title: str
    status: str
    created_at: float
    screenshot_path: Optional[str] = None


class BrowserManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.config_path = self.base_path / "configs" / "browser_config.yaml"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_config()
        self.driver = None
        self.playwright = None
        self.browser = None
        self.page = None
        self.sessions: Dict[str, BrowserSession] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            'on_navigate': [],
            'on_element_click': [],
            'on_form_submit': [],
        }
        
    def _load_config(self) -> BrowserConfig:
        if self.config_path.exists():
            try:
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    return BrowserConfig(**data)
            except Exception as e:
                logger.error(f"浏览器配置加载失败: {e}")
        return BrowserConfig()
    
    def save_config(self):
        try:
            import yaml
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config.__dict__, f, allow_unicode=True)
        except Exception as e:
            logger.error(f"浏览器配置保存失败: {e}")
    
    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()
    
    def start_browser(self) -> bool:
        if self.config.engine == "selenium":
            return self._start_selenium()
        elif self.config.engine == "playwright":
            return self._start_playwright()
        else:
            logger.error(f"不支持的浏览器引擎: {self.config.engine}")
            return False
    
    def _start_selenium(self) -> bool:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.firefox.service import Service as FirefoxService
            from selenium.webdriver.edge.service import Service as EdgeService
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.edge.options import Options as EdgeOptions
            
            if self.config.browser_type == "chrome":
                options = ChromeOptions()
                if self.config.headless:
                    options.add_argument("--headless")
                options.add_argument(f"--window-size={self.config.window_width},{self.config.window_height}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                
                if self.config.user_data_dir:
                    options.add_argument(f"--user-data-dir={self.config.user_data_dir}")
                if self.config.proxy:
                    options.add_argument(f"--proxy-server={self.config.proxy}")
                if self.config.user_agent:
                    options.add_argument(f"--user-agent={self.config.user_agent}")
                
                for arg in self.config.arguments:
                    options.add_argument(arg)
                
                for ext in self.config.extensions:
                    options.add_extension(ext)
                
                self.driver = webdriver.Chrome(options=options)
                
            elif self.config.browser_type == "firefox":
                options = FirefoxOptions()
                if self.config.headless:
                    options.add_argument("--headless")
                options.add_argument(f"--width={self.config.window_width}")
                options.add_argument(f"--height={self.config.window_height}")
                
                self.driver = webdriver.Firefox(options=options)
                
            elif self.config.browser_type == "edge":
                options = EdgeOptions()
                if self.config.headless:
                    options.add_argument("--headless")
                options.add_argument(f"--window-size={self.config.window_width},{self.config.window_height}")
                
                self.driver = webdriver.Edge(options=options)
            
            logger.info(f"Selenium {self.config.browser_type} 浏览器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"Selenium 浏览器启动失败: {e}")
            return False
    
    def _start_playwright(self) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            
            browser_type = self.config.browser_type
            launch_options = {
                "headless": self.config.headless,
            }
            
            if self.config.proxy:
                launch_options["proxy"] = {"server": self.config.proxy}
            
            if browser_type == "chrome" or browser_type == "edge":
                launch_options["args"] = [
                    f"--window-size={self.config.window_width},{self.config.window_height}"
                ] + self.config.arguments
                self.browser = self.playwright.chromium.launch(**launch_options)
            elif browser_type == "firefox":
                self.browser = self.playwright.firefox.launch(**launch_options)
            elif browser_type == "safari":
                self.browser = self.playwright.webkit.launch(**launch_options)
            
            context_options = {
                "viewport": {"width": self.config.window_width, "height": self.config.window_height}
            }
            
            if self.config.user_agent:
                context_options["user_agent"] = self.config.user_agent
            
            context = self.browser.new_context(**context_options)
            self.page = context.new_page()
            
            logger.info(f"Playwright {self.config.browser_type} 浏览器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"Playwright 浏览器启动失败: {e}")
            return False
    
    def navigate(self, url: str) -> bool:
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.get(url)
                self._trigger_callback('on_navigate', {'url': url, 'title': self.driver.title})
                return True
            elif self.config.engine == "playwright" and self.page:
                self.page.goto(url)
                self._trigger_callback('on_navigate', {'url': url, 'title': self.page.title()})
                return True
            return False
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False
    
    def get_current_url(self) -> str:
        if self.config.engine == "selenium" and self.driver:
            return self.driver.current_url
        elif self.config.engine == "playwright" and self.page:
            return self.page.url
        return ""
    
    def get_title(self) -> str:
        if self.config.engine == "selenium" and self.driver:
            return self.driver.title
        elif self.config.engine == "playwright" and self.page:
            return self.page.title()
        return ""
    
    def find_element(self, selector: str, by: str = "css") -> Any:
        try:
            if self.config.engine == "selenium" and self.driver:
                from selenium.webdriver.common.by import By
                by_map = {
                    "css": By.CSS_SELECTOR,
                    "id": By.ID,
                    "xpath": By.XPATH,
                    "name": By.NAME,
                    "class": By.CLASS_NAME,
                    "tag": By.TAG_NAME,
                }
                return self.driver.find_element(by_map.get(by, By.CSS_SELECTOR), selector)
            elif self.config.engine == "playwright" and self.page:
                return self.page.locator(selector)
            return None
        except Exception as e:
            logger.error(f"查找元素失败: {e}")
            return None
    
    def find_elements(self, selector: str, by: str = "css") -> List[Any]:
        try:
            if self.config.engine == "selenium" and self.driver:
                from selenium.webdriver.common.by import By
                by_map = {
                    "css": By.CSS_SELECTOR,
                    "id": By.ID,
                    "xpath": By.XPATH,
                    "name": By.NAME,
                    "class": By.CLASS_NAME,
                    "tag": By.TAG_NAME,
                }
                return self.driver.find_elements(by_map.get(by, By.CSS_SELECTOR), selector)
            elif self.config.engine == "playwright" and self.page:
                return self.page.locator(selector).all()
            return []
        except Exception as e:
            logger.error(f"查找元素失败: {e}")
            return []
    
    def click(self, selector: str, by: str = "css") -> bool:
        try:
            element = self.find_element(selector, by)
            if element:
                if self.config.engine == "selenium":
                    element.click()
                elif self.config.engine == "playwright":
                    element.click()
                self._trigger_callback('on_element_click', {'selector': selector})
                return True
            return False
        except Exception as e:
            logger.error(f"点击元素失败: {e}")
            return False
    
    def fill(self, selector: str, text: str, by: str = "css") -> bool:
        try:
            element = self.find_element(selector, by)
            if element:
                if self.config.engine == "selenium":
                    element.clear()
                    element.send_keys(text)
                elif self.config.engine == "playwright":
                    element.fill(text)
                return True
            return False
        except Exception as e:
            logger.error(f"填充表单失败: {e}")
            return False
    
    def submit_form(self, selector: str, by: str = "css") -> bool:
        try:
            element = self.find_element(selector, by)
            if element:
                if self.config.engine == "selenium":
                    element.submit()
                elif self.config.engine == "playwright":
                    element.press("Enter")
                self._trigger_callback('on_form_submit', {'selector': selector})
                return True
            return False
        except Exception as e:
            logger.error(f"提交表单失败: {e}")
            return False
    
    def execute_script(self, script: str) -> Any:
        try:
            if self.config.engine == "selenium" and self.driver:
                return self.driver.execute_script(script)
            elif self.config.engine == "playwright" and self.page:
                return self.page.evaluate(script)
            return None
        except Exception as e:
            logger.error(f"执行脚本失败: {e}")
            return None
    
    def screenshot(self, path: Optional[str] = None) -> Optional[str]:
        try:
            if path is None:
                screenshots_dir = self.base_path / "screenshots"
                screenshots_dir.mkdir(exist_ok=True)
                path = str(screenshots_dir / f"screenshot_{int(time.time())}.png")
            
            if self.config.engine == "selenium" and self.driver:
                self.driver.save_screenshot(path)
                return path
            elif self.config.engine == "playwright" and self.page:
                self.page.screenshot(path=path)
                return path
            return None
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def get_page_source(self) -> str:
        try:
            if self.config.engine == "selenium" and self.driver:
                return self.driver.page_source
            elif self.config.engine == "playwright" and self.page:
                return self.page.content()
            return ""
        except Exception as e:
            logger.error(f"获取页面源码失败: {e}")
            return ""
    
    def scroll_to(self, x: int, y: int):
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.execute_script(f"window.scrollTo({x}, {y});")
            elif self.config.engine == "playwright" and self.page:
                self.page.evaluate(f"window.scrollTo({x}, {y});")
        except Exception as e:
            logger.error(f"滚动失败: {e}")
    
    def scroll_to_element(self, selector: str, by: str = "css"):
        try:
            element = self.find_element(selector, by)
            if element:
                if self.config.engine == "selenium":
                    self.driver.execute_script("arguments[0].scrollIntoView();", element)
                elif self.config.engine == "playwright":
                    element.scroll_into_view_if_needed()
        except Exception as e:
            logger.error(f"滚动到元素失败: {e}")
    
    def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        try:
            if self.config.engine == "selenium" and self.driver:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return True
            elif self.config.engine == "playwright" and self.page:
                self.page.wait_for_selector(selector, timeout=timeout * 1000)
                return True
            return False
        except Exception as e:
            logger.error(f"等待元素超时: {e}")
            return False
    
    def go_back(self):
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.back()
            elif self.config.engine == "playwright" and self.page:
                self.page.go_back()
        except Exception as e:
            logger.error(f"后退失败: {e}")
    
    def go_forward(self):
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.forward()
            elif self.config.engine == "playwright" and self.page:
                self.page.go_forward()
        except Exception as e:
            logger.error(f"前进失败: {e}")
    
    def refresh(self):
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.refresh()
            elif self.config.engine == "playwright" and self.page:
                self.page.reload()
        except Exception as e:
            logger.error(f"刷新失败: {e}")
    
    def close(self):
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.quit()
                self.driver = None
            elif self.config.engine == "playwright":
                if self.browser:
                    self.browser.close()
                    self.browser = None
                if self.playwright:
                    self.playwright.stop()
                    self.playwright = None
                self.page = None
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
    
    def register_callback(self, event: str, callback: Callable):
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, data: Dict):
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")
    
    def is_running(self) -> bool:
        if self.config.engine == "selenium":
            return self.driver is not None
        elif self.config.engine == "playwright":
            return self.page is not None and self.browser is not None
        return False
    
    def get_cookies(self) -> List[Dict]:
        try:
            if self.config.engine == "selenium" and self.driver:
                return self.driver.get_cookies()
            elif self.config.engine == "playwright" and self.page:
                return self.page.context.cookies()
            return []
        except Exception as e:
            logger.error(f"获取Cookies失败: {e}")
            return []
    
    def set_cookies(self, cookies: List[Dict]):
        try:
            if self.config.engine == "selenium" and self.driver:
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            elif self.config.engine == "playwright" and self.page:
                self.page.context.add_cookies(cookies)
        except Exception as e:
            logger.error(f"设置Cookies失败: {e}")
    
    def clear_cookies(self):
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.delete_all_cookies()
            elif self.config.engine == "playwright" and self.page:
                self.page.context.clear_cookies()
        except Exception as e:
            logger.error(f"清除Cookies失败: {e}")
    
    def switch_to_frame(self, selector: str):
        try:
            if self.config.engine == "selenium" and self.driver:
                element = self.find_element(selector)
                if element:
                    self.driver.switch_to.frame(element)
            elif self.config.engine == "playwright":
                # Playwright handles frames differently
                pass
        except Exception as e:
            logger.error(f"切换Frame失败: {e}")
    
    def switch_to_default_content(self):
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.switch_to.default_content()
        except Exception as e:
            logger.error(f"切换默认内容失败: {e}")
