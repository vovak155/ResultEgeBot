import base64
import time
import telebot
import pandas as pd
import os
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from tabulate import tabulate

# Name = 'Владимир'
# Surname = 'Заболотский'
# patr = 'Андреевич'
# regcode = '611690964041'
# region = 'Кировская Область'
token = '5412870626:AAFyg7DERfOQkRS5NqJR7FOxnhQWoBRQFC4'
bot = telebot.TeleBot(token, threaded=False)


def pprint_df(dframe):
    return tabulate(dframe, headers='keys', showindex='False')


@bot.message_handler(commands=['start'])
def hello_user(message):
    bot.send_message(message.chat.id, 'Привет, ' + message.from_user.username + ", введи /help!")


@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.chat.id,
                     'Введите /check <Фамилия> <Имя> <Отчество> <Код регистрации>.\nПример: "/check Попов Иван Максимович 611690964041"')


URL = "https://checkege.rustest.ru/"
options: Options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')


@bot.message_handler(commands=['check'])
def check_result(message):
    def get_captcha_img():
        try:
            source_data = browser.page_source
            soup = bs(source_data, 'html.parser')
            elem = str(soup.find('div', class_='captcha')).split('"')
            img_data = elem[5]
            print('[INFO] Successfully parsed base64 img')
            return img_data
        except:
            print('[INFO] Get exception on parsing base64 img')
            pass

    def convert_img(uid):
        try:
            img_data = get_captcha_img()
            head, data = img_data.split(',', 1)
            file_ext = head.split(';')[0].split('/')[1]
            plain_data = base64.b64decode(data)
            with open(str(uid) + '.' + file_ext, 'wb') as f:
                f.write(plain_data)
            file = str(uid) + '.' + str(file_ext)
            print('[INFO] Successfully converted base64 image to jpeg image!')
            return str(file)
        except:
            print('[ERROR] Get exception on converting image!')
            pass

    def fillgaps(Surname, Name, patr, regcode, captcha):
        try:
            element = browser.find_element(By.ID, 'surname')
            element.send_keys(Surname)
            element = browser.find_element(By.ID, 'name')
            element.send_keys(Name)
            element = browser.find_element(By.ID, 'patr')
            element.send_keys(patr)
            element = browser.find_element(By.ID, 'regNum')
            element.send_keys(regcode)
            element = browser.find_element(By.ID, 'region_chosen')
            element.click()
            element = browser.find_element(By.XPATH, "//input[@tabindex='6']")
            element.send_keys('Кировская')
            element.send_keys(Keys.ENTER)
            # captcha = input(f'Please write your captcha:\n')
            element = browser.find_element(By.ID, 'captcha')
            element.send_keys(captcha)
        except Exception as Ex:
            print(Ex)

    def come_captcha(message):
        global captcha
        captcha = message.text
        bot.send_message(message.from_user.id, 'Вы ввели каптчу. Сейчас отправлю результаты ЕГЭ.')
        end_process()
    data = ['','','','','']
    uid = message.chat.id

    data = message.text.split(' ')
    if len(data) != 5:
        bot.send_message(uid, 'Вы неверно ввели команду. Используйте /help')
    else:
        if(len(str(data[4])) != 12):
            bot.send_message(uid, 'Вы неверно ввели код регистрации.')
        else:
            bot.send_message(uid, 'Сейчас отправлю картинку. Введите код с картинки:')
            Surname = data[1]
            Name = data[2]
            patr = data[3]
            regcode = data[4]
            browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            browser.get(URL)
            time.sleep(0.1)
            photo_path = convert_img(uid)
            bot.send_photo(uid, photo=open(str(photo_path), 'rb'))
            os.remove(str(uid) + '.jpeg')
            bot.register_next_step_handler(message, come_captcha)

    def end_process():
        try:
            fillgaps(Surname, Name, patr, regcode, captcha)
            submit = browser.find_element(By.ID, 'submit-btn')
            submit.click()
            time.sleep(1)
            ds = pd.read_html(browser.page_source)[0]
            with pd.option_context('display.max_rows', None, 'display.max_columns',
                                   None):  # more options can be specified also
                bot.send_message(chat_id=uid, text='<pre>' + pprint_df(ds) + '</pre>', parse_mode='HTML')
            # print(ds)
        except:
            bot.send_message(uid, 'Не удалось получить ответ с сервера. \nПроверьте правильность введенных данных. (/help)\n Попробуйте снова.')
        browser.quit()


if __name__ == '__main__':
    bot.infinity_polling()
