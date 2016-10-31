from os.path import join, splitext
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import shutil
import re
import requests
from tempfile import TemporaryDirectory
from time import sleep
from .gui import run_gui
from .programs import Upgrade as UpgradeProgram


class Upgrade:

    def __enter__(self):
        self.driver = webdriver.Firefox()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()

    def potential_urls(self, fn, number):
        d = self.driver
        d.get("https://images.google.com")
        d.find_element_by_css_selector('span#qbi').click()
        d.find_element_by_link_text('Upload an image').click()
        d.find_element_by_css_selector('input#qbfile').send_keys(fn)

        while True:
            try:
                d.find_element_by_link_text('All sizes').click()
                break
            except NoSuchElementException:
                sleep(1)

        imgs = []
        while True:
            imgs = d.find_elements_by_class_name('rg_ic')
            if imgs: break
            sleep(1)

        urls = []
        for i in imgs[:number]:
            i.click()
            sleep(1)
            elems = d.find_elements_by_link_text('View image')
            for e in elems:
                p = e.find_element_by_xpath('..')
                html = p.get_attribute('innerHTML')
                match = re.search('href="(?P<url>[^"]*)"', html)
                if match:
                    url = match.group('url')
                    if url not in urls:
                        urls.append(match.group('url'))

        return urls
