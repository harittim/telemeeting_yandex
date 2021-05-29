# -*- coding: utf-8 -*-
import telebot
import time
from telebot import types
import datetime as dt
import json
from flask import Flask, request
from bs4 import BeautifulSoup
import requests
from data import db_session
from data.users import User
import yadisk
import os


class Teleschool:
    def __init__(self):
        API_TOKEN = 'Token'
        db_session.global_init("db/blogs.db")
        self.db_sess = db_session.create_session()
        self.profile_status = {'name': {'reg_status': 'login_part_name', 'ch_status': 'change_name',
                                        'question': 'Напиши мне свое полное имя.\n\n*Например:* Тимофей\n\nЕсли ты допустил ошибку, не переживай, все поля можно поправить после регистрации.', 'ch_question': 'Напиши мне свое полное имя.\n\n*Например:* Тимофей', 'next': 'surname',
                                        'name': 'Имя', 'required': True, 'choice' : False, 'type': 'message'},
                               'surname': {'reg_status': 'login_part_surname', 'ch_status': 'change_surname',
                                           'question': 'А какая у тебя фамилия?\n\n*Например:* Харитонов ', 'ch_question': 'А какая у тебя фамилия?\n\n*Например:* Харитонов ', 'next': 'photo',
                                           'name': 'Фамилия', 'required': True, 'choice' : False, 'type': 'message'},
                                'photo':{'name': 'Фото','reg_status': 'login_part_photo', 'ch_status': 'change_photo', 'required': True, 'choice' : False,
                                           'question': 'Отправь мне свою фотографию в формате файла. Я знаю, ты справишься💪', 'ch_question': 'Отправь мне свою фотографию в формате файла. Я знаю, ты справишься💪','next': 'relationship', 'type': 'photo'},
                                'relationship': {'reg_status': 'login_part_relationship', 'ch_status': 'change_relationship',
                                           'question': 'А откуда ты знаешь Галю или Даниила? Выбери один из вариантов:', 'ch_question': 'Откуда ты знаешь Галю или Даниила? Выбери один из вариантов:', 'next': 'history',
                                           'name': 'Связи с женихом и невестой', 'required': True, 'choice' : True, 'type': 'message', 'choices': {'relationship_friends' : 'Друзья', 'relationship_husband_relatives' : 'Родные жениха', 'relationship_wif_relatives' : 'Родные невесты', 'relationship_own_choise' : 'Свой вариант'}},
                               'history': {'reg_status': 'login_part_history', 'ch_status': 'change_history',
                                            'question': 'Расскажи, какую-нибудь историю - как ты познакомился с Галей или Даниилом; забавную историю связанную с Галей или Даниилом.',  'ch_question': 'Расскажи, какую-нибудь историю - как ты познакомился с Галей или Даниилом; забавную историю связанную с Галей или Даниилом.',
                                            'next': 'about', 'name': 'История знакомства', 'required': False, 'choice' : False, 'type': 'message'},
                                'about': {'reg_status': 'login_part_about', 'ch_status': 'change_about',
                                            'question': 'Давай познакомимся еще ближе😊\nНапиши мне пару слов о себе, например, чем ты занимаешься.', 'ch_question': 'Напиши мне пару слов о себе, например, чем ты занимаешься.',
                                            'next': 'pending', 'name': 'О себе', 'required': False, 'choice' : False, 'type': 'message'}}
        self.bot = telebot.TeleBot(API_TOKEN, threaded=False)

        self.bot.message_handler(func=lambda message: True, content_types='text')(self.message_respond)
        self.bot.callback_query_handler(func=lambda call: True)(self.call_respond)
        self.bot.message_handler(func=lambda message: True, content_types='document')(self.document_respond)
        self.bot.message_handler(func=lambda message: True, content_types='video')(self.video_respond)

        self.keyboard_color = types.InlineKeyboardMarkup()
        keyboard_color_1 = types.InlineKeyboardButton(text="Изменить профиль", callback_data='change_users')
        self.keyboard_color.add(keyboard_color_1)

    def video_respond(self, message):
        user = self.db_sess.query(User).filter(User.id == message.chat.id).first()

        if user.status == 'verified':
            json_data = open('photo_num.txt')
            a = json.load(json_data)
            json_data.close()
            file_info = self.bot.get_file(message.json['video']['file_id'])
            downloaded_file = self.bot.download_file(file_info.file_path)
            src = '/home/harittim/Telemeetting/photo_exp/' + str(message.chat.id) + '.mp4'
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)
            y = yadisk.YaDisk(token='token')
            y.upload(src, '/Telemeetting/' + str(a) + '.mp4')
            a += 1
            with open('photo_num.txt', 'w') as outfile:
                json.dump(a, outfile)
            outfile.close()
            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), src)
            os.remove(path)
            self.bot.send_message(message.chat.id, 'Успешно загруженно.')


    def message_respond(self, message):
        if not self.db_sess.query(User).filter(User.id == message.chat.id).first():
            if message.text == '/start':
                self.start_message(message)
        else:
            user = self.db_sess.query(User).filter(User.id == message.chat.id).first()
            if message.text == '/start':
                self.start_message(message)
            elif user.status == 'pending':
                self.bot.send_message(message.chat.id, 'Доступ запрошен. Ожидайте подтверждения администратора.')
            elif user.status[:5] == 'login':
                if self.profile_status[user.status[11:]]['type'] == 'message':
                    self.login(message.chat.id, message.text, 'mes')
                elif self.profile_status[user.status[11:]]['type'] == 'photo':
                    self.bot.send_message(message.chat.id, self.profile_status[user.status[11:]]['question'] )
                else:
                    self.bot.send_message(message.chat.id, 'Что то не так. Пожалуйста обратитесь @harittim' )
            elif user.status == 'verified' or user.status[:6] == 'change':
                if message.text == '📸 Фото и видео':
                    user.status = 'verified'
                    self.bot.send_message(message.chat.id, '📸Я собираю все фотографии от гостей в эту [папочку](https://disk.yandex.ru/d/CnzzUcZHsVfFOw).\n\nБудет классно, если ты тоже поделишься своими фото. Просто отправь мне фото и видео в формате файла. Я все сохраню🤝', parse_mode='Markdown')
                elif message.text == '🗿 Профиль':
                    user.status = 'verified'
                    self.profile(message.chat.id, message.chat.id, True)
                elif message.text == '🤵👰Подробнее о свадьбе':
                    keyboard_start = types.InlineKeyboardMarkup()
                    keyboard_start_1 = types.InlineKeyboardButton(text='Погода ⛅', callback_data='more_info_weather' )
                    keyboard_start.add(keyboard_start_1)
                    keyboard_start_1 = types.InlineKeyboardButton(text='Идеи для подарков 🎁', callback_data='more_info_idea_for_gifts')
                    keyboard_start.add(keyboard_start_1)
                    self.bot.send_message(message.chat.id, '🤵👰Подробнее о свадьбе', reply_markup=keyboard_start)
                elif message.text == '👨‍👩‍👧‍👦Гости':
                    keyboard_start = types.InlineKeyboardMarkup()
                    for key in self.profile_status['relationship']['choices']:
                        keyboard_start_1 = types.InlineKeyboardButton(text=self.profile_status['relationship']['choices'][key], callback_data='show_list.' + key + '.0' )
                        keyboard_start.add(keyboard_start_1)
                    self.bot.send_message(message.chat.id, 'Кого вы хотите посмотреть?', reply_markup=keyboard_start)
                elif user.status[:6] == 'change':
                    self.change(message.chat.id, message.text, 'mes')
            self.db_sess.commit()

    def profile(self, iden_info, iden, keyboard):
        mes = ''
        keyboard_start = types.InlineKeyboardMarkup()
        for keys in self.profile_status:
            keyboard_start_1 = types.InlineKeyboardButton(text=self.profile_status[keys]['name']  , callback_data=self.profile_status[keys]['ch_status'] )
            keyboard_start.add(keyboard_start_1)
        src = '/home/harittim/Telemeetting/users_photo/'  + str(iden_info) + '.jpg'
        user_img = open(src, 'rb')
        user = self.db_sess.query(User).filter(User.id == iden_info).first()
        mes += user.name + ' ' + user.surname + '\n' + user.relationship + '\n*Небольшая история:*\n' + user.history + '\n*О себе:*\n' + user.about
        if keyboard:
            self.bot.send_photo(iden, user_img, mes, reply_markup=keyboard_start, parse_mode='Markdown')
        else:
            self.bot.send_photo(iden, user_img, mes, parse_mode='Markdown')


    def call_respond(self, call):
        user = self.db_sess.query(User).filter(User.id == call.from_user.id).first()
        if call.data[:5] == 'skip_' and user.status[11:] == call.data[5:]:
            self.login(call.from_user.id, 'skiped', 'mes')
        elif user.status[11:] == 'relationship' and call.data[:12] == 'relationship':
            if call.data == 'relationship_own_choise':
                self.bot.send_message(call.from_user.id, 'Напишите свой вариант.')
            else:
                self.login(call.from_user.id, self.profile_status['relationship']['choices'][call.data], 'mes')
        elif user.status == 'verified':
            if call.data[:6] == 'change':
                iden = call.from_user.id
                user.status = call.data
                next_key = call.data[7:]
                if self.profile_status[next_key]['choice']:
                    keybord = types.InlineKeyboardMarkup()
                    for keys in self.profile_status[next_key]['choices']:
                        keyboard_color_1 = types.InlineKeyboardButton(text=self.profile_status[next_key]['choices'][keys], callback_data=keys)
                        keybord.add(keyboard_color_1)
                
                    self.bot.send_message(iden, self.profile_status[next_key]['ch_question'], parse_mode='Markdown', reply_markup=keybord)
                else:
                    self.bot.send_message(iden, self.profile_status[next_key]['ch_question'], parse_mode='Markdown')
            elif call.data[:9] == 'show_list':
                step = 2
                a = call.data.split('.')
                type_of = a[1]
                num = int(a[2])
                if type_of != 'relationship_own_choise':
                    users = self.db_sess.query(User).filter(User.relationship == self.profile_status['relationship']['choices'][a[1]], User.status == 'verified').all()
                else:
                    users = self.db_sess.query(User).filter(User.relationship != 'Друзья', User.relationship != 'Родные жениха', User.relationship != 'Родные невесты', User.status == 'verified').all()
                if len(users) > num:
                    keyboard_start = types.InlineKeyboardMarkup()
                    a = len(users)
                    if len(users) > num + step:
                        a = num + step
                    for i in range(num, a):
                        user = users[i]
                        keyboard_start_1 = types.InlineKeyboardButton(text=user.name + ' ' + user.surname, callback_data='show_user_' + str(user.id))
                        keyboard_start.add(keyboard_start_1)
                    if len(users) > num + step:
                        keyboard_start_1 = types.InlineKeyboardButton(text='Больше гостей 👨‍👩‍👧‍👦', callback_data='show_list.' + type_of  + '.' + str(num + step) )
                        keyboard_start.add(keyboard_start_1)
                    self.bot.send_message(call.from_user.id, self.profile_status['relationship']['choices'][type_of], reply_markup=keyboard_start, parse_mode='Markdown')
                else:
                    self.bot.send_message(call.from_user.id, 'Пока нет зарегистрированных гостей' , parse_mode='Markdown')
            elif call.data[:10] == 'show_user_':
                self.profile(call.data[10:], call.from_user.id, False)
                
            elif call.data == 'more_info_weather':
                month = 'july'
                a = self.weather(month, 17)
                link = '[Яндекс Погоды](https://yandex.ru/pogoda/cheboksary/month/' + month + '?via=cnav&slug=cheboksary)'
                wind = str(a['wind']).split('.')
                text = 'По данным ' + link + ' 17 июля 2021 будет: \n'
                if a['max_day_t'] < 0:
                    if a['prec_prob'] > 50:
                        text += '❄' * 10 + '\n'
                    else:
                        text += '🌤️' * 10 + '\n'
                else:
                    if a['prec_prob'] > 50:
                        text += '⛈️' * 10 + '\n'
                    else:
                        text += '🌤️' * 10 + '\n'
                text += '*Температура:* ' + '\\' + str(a['max_day_t']) + '\n' + '*Ветер:* ' + wind[0] + '\\.' + wind[
                    1] + ' м\/с\\.\n *Вероятность осадков:* ' + str(a['prec_prob']) + '\%\.'
                print(text)
                self.bot.send_message(call.from_user.id, text, parse_mode='MarkdownV2')
            elif call.data == 'more_info_idea_for_gifts':
                self.bot.send_message(call.from_user.id, '<Текст>')
        elif user.status == 'change_relationship':
            if call.data == 'relationship_own_choise':
                self.bot.send_message(call.from_user.id, 'Напишите свой вариант.')
            elif call.data[:12] == 'relationship':
                self.change(call.from_user.id,  self.profile_status['relationship']['choices'][call.data], 'mes')
        self.db_sess.commit()

    def document_respond(self, message):
        user = self.db_sess.query(User).filter(User.id == message.chat.id).first()
        if user.status == 'login_part_photo':
            self.login(message.chat.id, message, 'photo')
        elif user.status == 'change_photo':
            self.change(message.chat.id, message, 'photo')
        elif user.status == 'verified':
            json_data = open('photo_num.txt')
            a = json.load(json_data)
            json_data.close()
            file_info = self.bot.get_file(message.json['document']['file_id'])
            downloaded_file = self.bot.download_file(file_info.file_path)
            src = '/home/harittim/Telemeetting/photo_exp/' + str(message.chat.id) + '.jpg'
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)
            y = yadisk.YaDisk(token='Token')
            y.upload(src, '/Telemeetting/' + str(a) + '.jpg')
            a += 1
            with open('photo_num.txt', 'w') as outfile:
                json.dump(a, outfile)
            outfile.close()
            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), src)
            os.remove(path)
            self.bot.send_message(message.chat.id, 'Успешно загруженно.')
          
    def menu(self, message):
        user_markup = types.ReplyKeyboardMarkup(True, False)
        user_markup.row('Профиль', 'Фотографии', 'Погода на мероприятии')
        self.bot.send_message(message, 'Главное меню:', reply_markup=user_markup)

    def start_message(self, message):
        self.bot.send_message(message.chat.id, 'Привет, меня зовут <name>.\n\nЯ бот-помощник на свадьбе у Даниила и Гали.\nСкорее регистрируйся, мне столько всего нужно тебе рассказать 😍\nЕсли возникнут трудности пиши @harittim😉')
        if not self.db_sess.query(User).filter(User.id == message.chat.id).first():
            user = User()
            user.id = message.chat.id
            user.status = 'login_part_name'
            self.db_sess.add(user)
        else:
            user = self.db_sess.query(User).filter(User.id == message.chat.id).first()
            user.status = 'login_part_name'
        self.db_sess.commit()
        self.bot.send_message(message.chat.id, self.profile_status['name']['question'], parse_mode='Markdown')


    def db_write(self, iden, param, a):
        if param == 'name':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            user.name = a
        if param == 'surname':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            user.surname = a
        if param == 'relationship':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            user.relationship = a
        if param == 'history':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            user.history = a
        if param == 'about':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            user.about = a
        self.db_sess.commit()

    def db_back(self, iden, param):
        if param == 'name':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            return user.name
        if param == 'surname':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            return user.surname
        if param == 'relationship':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            return user.relationship
        if param == 'history':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            return user.history
        if param == 'about':
            user = self.db_sess.query(User).filter(User.id == iden).first()
            return user.about

    def admins_r(self):
        json_data = open('/home/harittim/Telemeetting_manager/admins.txt')
        users_status_tmp = json.load(json_data)
        json_data.close()
        return users_status_tmp

    def weather(self, month, day):
        req = requests.get("https://yandex.ru/pogoda/cheboksary/month/" + month,
                           headers={'User-Agent': 'Mozilla/5.0'})

        soup = BeautifulSoup(req.text, "lxml")
        temp = soup.find_all('section', attrs={'class': 'content__section content__section_climate-graph_yes'})
        data = soup.find('div', attrs={'class': 'climate-graph i-bem'})
        tmp = json.loads(data['data-bem'])['climate-graph']['graphData']
        if tmp[day - 1]['day'] == day:
            return tmp[day - 1]

    def change(self, iden, answer, typ):
        user = self.db_sess.query(User).filter(User.id == iden).first()
        if typ == 'mes':
            self.db_write(iden, user.status[7:], answer)
            user.status = 'verified'
            self.db_sess.commit()
        elif typ == 'photo':
            file_info = self.bot.get_file(answer.json['document']['file_id'])
            downloaded_file = self.bot.download_file(file_info.file_path)
            src = '/home/harittim/Telemeetting/users_photo/' + str(iden) + '.jpg'
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)
            user.status = 'verified'
            self.db_sess.commit()  
        self.profile(iden, iden, True)
            

    def login(self, iden, answer, typ):
         
        user = self.db_sess.query(User).filter(User.id == iden).first()
        for keys in self.profile_status:
                if self.profile_status[keys]['reg_status'] == user.status:
                    key = keys
                    break
        if typ == 'mes':
            self.db_write(iden, key, answer)
        elif typ == 'photo':
            file_info = self.bot.get_file(answer.json['document']['file_id'])
            downloaded_file = self.bot.download_file(file_info.file_path)
            src = '/home/harittim/Telemeetting/users_photo/' + str(iden) + '.jpg'
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)
        next_key = self.profile_status[key]['next']
        if next_key != 'pending':
            user.status = self.profile_status[next_key]['reg_status']
            if self.profile_status[next_key]['required']:
                if self.profile_status[next_key]['choice']:
                    keybord = types.InlineKeyboardMarkup()
                    for keys in self.profile_status[next_key]['choices']:
                        keyboard_color_1 = types.InlineKeyboardButton(text=self.profile_status[next_key]['choices'][keys], callback_data=keys)
                        keybord.add(keyboard_color_1)
                
                    self.bot.send_message(iden, self.profile_status[next_key]['question'], parse_mode='Markdown', reply_markup=keybord)
                else:
                    self.bot.send_message(iden, self.profile_status[next_key]['question'], parse_mode='Markdown')
            else:
                keyboard_start = types.InlineKeyboardMarkup()
                if self.profile_status[next_key]['choice']:
                    for keys in self.profile_status[next_key]['choices']:
                        keyboard_color_1 = types.InlineKeyboardButton(text=keys, callback_data=self.profile_status[next_key]['choices'][keys])
                        keyboard_start.add(keyboard_color_1)
                
                keyboard_start_1 = types.InlineKeyboardButton(text='Пропустить', callback_data='skip_' + next_key)
                keyboard_start.add(keyboard_start_1)
                self.bot.send_message(iden, self.profile_status[next_key]['question'], parse_mode='Markdown', reply_markup=keyboard_start)
        else:
            user = self.db_sess.query(User).filter(User.id == iden).first()
            user.status = 'pending'
            api = 'Token'
            bot = telebot.TeleBot(api, threaded=False)
            keyboard_start = types.InlineKeyboardMarkup()
            keyboard_start_1 = types.InlineKeyboardButton(text='Добавить', callback_data='add_user_' + str(iden))
            keyboard_start_2 = types.InlineKeyboardButton(text='Отклонить', callback_data='no_user_' + str(iden))
            keyboard_start.add(keyboard_start_1,keyboard_start_2)
            user = self.db_sess.query(User).filter(User.id == iden).first()
            mes = user.name + ' ' + user.surname + '\n' + user.relationship + '\n*Небольшая история:*\n' + user.history + '\n*О себе:*\n' + user.about
            src = '/home/harittim/Telemeetting/users_photo/' + str(iden) + '.jpg'
            user_img = open(src, 'rb')
            admin = self.admins_r()
            for i in admin.keys():
                bot.send_photo(int(i), user_img, mes, reply_markup=keyboard_start, parse_mode='Markdown')
                self.bot.send_message(iden, 'Спасибо за твоё время. Я скоро тебе напишу.')
        self.db_sess.commit()  

Teleschool = Teleschool()

app = Flask(__name__)
app.debug = True

URL = '130.193.50.133:443/Telemeetting/HOOK'


# Set_webhook
@app.route('/Telemeetting/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    print('\n...webhook_setup...\n')
    try:

        s = Teleschool.bot.set_webhook('https://{}'.format(URL), certificate=open('/etc/ssl/server.crt', 'rb'))
        if s:
            print('\n printing on site: webhook setup ok \n')
            return "webhook setup ok"
        else:
            return "webhook setup failed"
    except Exception as e:
        print(e)


@app.route('/Telemeetting/')
def index():
    return '<h1>Hello_telemeettin_</h1>'


@app.route('/Telemeetting/HOOK', methods=['POST', 'GET'])
def webhook_handler():
    if request.method == "POST":
        try:
            update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
            print('\n{}\n'.format(update))
            Teleschool.bot.process_new_updates([update])
        except Exception as e:
            print(e)
    return 'ok'
