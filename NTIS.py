from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import pymysql
from time import sleep
import random
from set_info import *

options = webdriver.ChromeOptions()


class NTIS_Crawler:
    def __init__(self, db_info=account['DB'], login_info=account['NTIS'], driver_loc=account['driver']['loc']):
        self.db_info=db_info
        self.login_info=login_info
        self.driver=webdriver.Chrome(driver_loc)
        self.setNTIS()
        print(self.html)

    def closePopup(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.find_element_by_xpath("""/html/body/div/div/div[2]/div[2]/label""").click()
        self.driver.find_element_by_xpath("""//*[@id="btnClose2"]""").click()
        self.driver.switch_to.window(self.driver.window_handles[0])


    def setNTIS(self):
        self.driver.get('https://www.ntis.go.kr/ThMain.do')
        element = self.driver.find_element_by_xpath("/html/body/div[4]/div/div[2]/div[1]/button")
        self.driver.execute_script("arguments[0].click();", element)
        # 로그인 팝업 창으로 변경
        self.driver.switch_to.window(self.driver.window_handles[-1])
        # input id
        elem_login = self.driver.find_element_by_xpath("""/html/body/div/form/label[2]/input""")
        elem_login.clear()
        elem_login.send_keys(self.login_info['id'])
        # input pw
        elem_login = self.driver.find_element_by_xpath("""/html/body/div/form/label[4]/input""")
        elem_login.clear()
        elem_login.send_keys(self.login_info['password'])
        #elem_login.send_keys(Keys.RETURN)
        # click login button 
        xpath = """/html/body/div/form/input"""
        self.driver.find_element_by_xpath(xpath).click()
        # change main window
        self.driver.switch_to.window(self.driver.window_handles[0])


    def crawl(option):
        if crawl==



    def crawlPid(keyword_seq):
        pass

    def crawlPjt():
        pass

    def crawlBus():
        pass

    def crawlCommer():
        pass

    def crawlResearchFee():
        pass

    def crawlRoyalfee():
        pass



