from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from urllib.parse import quote
from urllib import request
import time
import warnings
import json
import datetime
warnings.filterwarnings('ignore')

def login(driver, userName, password, retry=0):
    if retry == 3:
        raise Exception('EPE login failed')

    print('Trying to login EPE...')

    driver.get('https://epe.pku.edu.cn/venue/pku/Login')
    driver.get(
        f'https://epe.pku.edu.cn/ggtypt/login?service=https://epe.pku.edu.cn/venue-server/loginto')
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'logon_button')))
    driver.find_element_by_id('user_name').send_keys(userName)
    time.sleep(0.1)
    driver.find_element_by_id('password').send_keys(password)
    time.sleep(0.1)
    driver.find_element_by_id('logon_button').click()
    try:
        WebDriverWait(driver,
                      10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'isLoginContent')))
        print('EPE login succeeded！')
    except:
        print('Retrying...')
        login(driver, userName, password, retry + 1)
    


def go_to_venue(driver):
    # driver.get('https://epe.pku.edu.cn/venue/pku/venue-introduce')
    # WebDriverWait(driver, 10).until(
    #     EC.visibility_of_element_located((By.CLASS_NAME, 'searchCondition')))
    # driver.find_elements_by_class_name('venueDetailBottomItem')[2].click()
    print('Getting into the venue page...')
    driver.get('https://epe.pku.edu.cn/venue/pku/venue-reservation/115')
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'reserveBlock')))
    print('In the venue page now.')


# date: DD in YYYY-MM-DD
def get_date(driver, date):
    TOTAL_DATE_CELLS = 42
    DAYS_IN_MONTH = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # the day this is written, no any meaning here
    date_to_do = datetime.date(2021, 11, 24)
    today = date_to_do.today()
    if date >= today.day:
        date_to_do = datetime.date(today.year, today.month, date)
    else:
        if today.month == 12:
            date_to_do = datetime.date(today.year + 1, 1, date)
        else:
            date_to_do = datetime.date(today.year, today.month + 1, date)

    # 0~6 for Sun, Mon, ..., Sat
    weekday_1st = (datetime.date(today.year, today.month, 1).weekday() + 1) % 7
    if date >= today.day:
        cell_no = weekday_1st + date - 1
    else:
        cell_no = weekday_1st + DAYS_IN_MONTH[today.month] + date - 1
        print(cell_no)

    while True:
        # Open date selector
        driver.find_element_by_class_name('ivu-input').click()
        # Wait for date selector
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'ivu-select-dropdown')))
        
        # Several types of cells:
        # ivu-date-picker-cells-cell: Normal cell
        # ivu-date-picker-cells-cell ivu-date-picker-cells-cell-prev-month: Cell for last month
        # ivu-date-picker-cells-cell ivu-date-picker-cells-cell-selected ivu-date-picker-cells-cell-today ivu-date-picker-cells-focused: Cell for today, picked
        # ivu-date-picker-cells-cell ivu-date-picker-cells-cell-disabled: Cells for this month's upcoming days
        # ivu-date-picker-cells-cell ivu-date-picker-cells-cell-disabled ivu-date-picker-cells-cell-next-month: Cells for next month
        disabled_date_picker_cells = driver.find_elements_by_class_name('ivu-date-picker-cells-cell.ivu-date-picker-cells-cell-disabled')
        
        # detect if reservation for the given date is opened
        if len(disabled_date_picker_cells) >= TOTAL_DATE_CELLS - cell_no:
            
            # since the refresh button aside the date input-box has no effect
            # driver.find_elements_by_class_name('btnMaring')[2].click()

            driver.refresh()

            print(f'Reservation for {date_to_do} not opened yet. Refresh the whole page')

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'reserveBlock')))
        else:
            # select date, detect if the date has been selected, and retry if necessary
            tryTime = 0
            while tryTime < 10:
                print(f'trying to select date {date_to_do}')
                date_picker_cells = driver.find_elements_by_class_name('ivu-date-picker-cells-cell')
                date_picker_cells[cell_no].click()
            
                time.sleep(0.05)
                date_picker_cells = driver.find_elements_by_class_name('ivu-date-picker-cells-cell')
                if 'selected' in date_picker_cells[cell_no].get_attribute('class'):
                    break
                tryTime += 1
            else:
                print('failed')
                return
            
            # may cause bug here?
            # since I don't know after the date is changed, whether there's any
            #  'reserveBlock'
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'reserveBlock')))
            print(f'date {date_to_do} selected!')
            # screen_capture(driver, '0.png')
            break


# 8~9 for block 0, etc. until block 13.
def reserve(driver, times, phone_number):
    # @param times: str in format like '8-10', '20-22'
    # @param phone_number: str
    # Types: "reserveBlock position reserved"
    #        "reserveBlock position disabled"
    #        "reserveBlock position free"
    #        "reserveBlock position free selected"

    times = [int(i)-8 for i in times.split('-')]
    blocks = list(range(times[0], times[1]))
    selected_block = 0
    
    for i in range(len(blocks)):
        if selected_block >= 2:
            break
        reserveBlocks = driver.find_elements_by_class_name('reserveBlock.position')
        
        b = blocks[i]
        if 'free' not in reserveBlocks[b].get_attribute('class'):
            print(f'block {b} is not available:', reserveBlocks[b].get_attribute('class'))
            continue

        tryTime = 0
        while tryTime < 3:
            print(f'trying to select block {b}, which is for {b+8}:00~{b+9}:00')
            reserveBlocks[b].click()
            time.sleep(0.05)
            reserveBlocks = driver.find_elements_by_class_name('reserveBlock.position')
            if 'selected' in reserveBlocks[b].get_attribute('class'):
                selected_block += 1
                break
            tryTime += 1
        else:
            print('selection failed for block {b}, which is for {b+8}:00~{b+9}:00')
            continue

    if selected_block == 0:
        print('no block selected. reserve failed.')
        return

    # check-box for "I've read license"
    driver.find_element_by_class_name('ivu-checkbox-input').click()
    time.sleep(0.05)

    # click submit for step 1
    submitButton = driver.find_elements_by_class_name('payHandleItem')[1]
    print("step1:", submitButton.text)
    driver.find_elements_by_class_name('payHandleItem')[1].click()
    
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'reservation-step-two')))
        
    # input phone number
    # influenced by browser cookie here
    # driver.find_element_by_class_name('ivu-input.ivu-input-default').send_keys(phone_number)
    # time.sleep(0.05)
    
    # click submit for step 2

    submitButton = driver.find_elements_by_class_name('payHandleItem')[1]
    print("step2:", submitButton.text)
    submitButton.click()
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'payMent')))
    except:
        print('reserve failed.')
        screen_capture(driver, 'failure.png')
        return
    print('reserved!')
    screen_capture(driver, 'success.png')


def screen_capture(driver, filename):
    # driver.maximize_window()
    driver.set_window_size(1920,1920)
    time.sleep(0.1)
    driver.save_screenshot(f'./{filename}')
    print(f'Screenshot {filename} saved')


def run(driver, userName, password, date, time_to_reserve, phone_number):
    login(driver, userName, password)
    print('=================================')
    go_to_venue(driver)
    print('=================================')
    get_date(driver, date)
    print('=================================')
    reserve(driver, time_to_reserve, phone_number)
    print('=================================')



if __name__ == '__main__':
    pass
