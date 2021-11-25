# -*- coding: utf-8
import env_check
from configparser import ConfigParser
from selenium.webdriver.chrome.options import Options
from func import *
import warnings
import sys
import os
import re
warnings.filterwarnings('ignore')


def sys_path(browser):
    path = f'./{browser}/'
    if sys.platform.startswith('win'):
        return path + f'{browser}.exe'
    elif sys.platform.startswith('linux'):
        return path + f'{browser}'
    elif sys.platform.startswith('darwin'):
        return path + f'{browser}'
    else:
        raise Exception('暂不支持该系统')


def go(config):
    conf = ConfigParser()
    conf.read(config, encoding='utf8')

    userName, password = dict(conf['login']).values()
    date, time_to_reserve = dict(conf['date_time']).values()
    date = int(date)
    phone_number, = dict(conf['phone_number']).values()
    

    run(driver_pjs, userName, password, date, time_to_reserve, phone_number)


if __name__ == '__main__':

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver_pjs = webdriver.Chrome(
            options=chrome_options,
            executable_path=sys_path(browser="chromedriver"),
            service_args=['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1'])
    print('Driver Launched\n')

    go('config.ini')

    driver_pjs.quit()
