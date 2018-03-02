from flask import Flask, request, make_response
from pyfiglet import Figlet
import json
import os
import sys
import telebot
from telebot import types
import config

server = Flask(__name__)
bot = telebot.TeleBot(config.API_TOKEN)
figlet = Figlet()

def get_all_texts(figlet, text, fonts):
    all_texts = {}
    for font in fonts:
        figlet.setFont(font=font)
        all_texts[font] = ""
        current_font_text = ""
        for char in text:
            try:
                ascii_char = figlet.renderText(char)
            except Exception as err:
                break
            current_font_text += "{}\n".format(ascii_char)

        all_texts[font] = current_font_text

    return all_texts


def search_fonts(search_term, fonts, max_elements):
    if search_term is None:
        search_term = ""
    return [font for font in fonts if search_term in font][:max_elements]


def parse_query(query):
    if (query == ""):
        return False

    result = {'text': None, 'search_term': None}
    split_query = query.split(' ')
    if (len(split_query) == 1):
        result['text'] = split_query[0]
    elif (len(split_query) > 1):
        result['text'] = split_query[0]
        result['search_term'] = split_query[1]

    return result


def build_query_results(texts):
    rs = []
    id = 0
    for font, text in texts.iteritems():
        id += 1
        rs.append(types.InlineQueryResultArticle(
            str(id),
            font,
            types.InputTextMessageContent(
                "```{}```".format(text),
                parse_mode='Markdown'
            )
        ))

    return rs


@bot.inline_handler(lambda query: True)
def default_query(inline_query):
    query = inline_query.query
    result = parse_query(query)
    if not result:
        return

    search_term = result['search_term']
    text = result['text']

    fonts = search_fonts(search_term, config.ALLOWED_FONTS, 10)
    all_texts = get_all_texts(figlet, text, fonts)
    query_results = build_query_results(all_texts)
    bot.answer_inline_query(inline_query.id, query_results, cache_time=2592000)


@server.route("{subpath}/bot".format(subpath=config.NGINX_SUBPATH), methods=['POST'])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("{subpath}/".format(subpath=config.NGINX_SUBPATH))
def webhook():
    webhook = bot.get_webhook_info()
    bot.remove_webhook()
    bot.set_webhook(url="{hostname}{subpath}/bot".format(hostname=config.WEBHOOK_URL, subpath=config.NGINX_SUBPATH))
    return "!", 200


if (len(sys.argv) == 2):
    if (config.POLLING):
        bot.remove_webhook()
        bot.polling()
    else:
        server.run(host="0.0.0.0", port=os.environ.get('PORT', 9999))
