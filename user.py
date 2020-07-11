import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN, PAY_TIMEOUT, PAYMENT_METHOD
import sqlite3
import time
import datetime
import random
import importlib


ROUTE, CATEGORY, PRICE, SUBMIT, TRADE, CHOOSE_PAYMENT_METHOD = range(6)
bot = telegram.Bot(token=TOKEN)


def start(update, context):
    print('进入start函数')
    keyboard = [
        [InlineKeyboardButton("购买商品", callback_data=str('购买商品')),
         InlineKeyboardButton("查询订单", callback_data=str('查询订单'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        '选择您的操作：',
        reply_markup=reply_markup
    )
    return ROUTE


def category_filter(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from category ORDER BY priority")
    categorys = cursor.fetchall()
    conn.close()
    for i in categorys:
        category_list = [InlineKeyboardButton(i[1], callback_data=str(i[1]))]
        keyboard.append(category_list)
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="选择分类",
        reply_markup=reply_markup
    )
    return CATEGORY


def goods_filter(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    category_name = update.callback_query.data
    context.user_data['category_name'] = category_name
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from goods where category_name=? and status=? ORDER BY priority",
                   (category_name, 'active',))
    goods = cursor.fetchall()
    for i in goods:
        goods_id = i[0]
        cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'active'))
        active_cards = cursor.fetchall()
        cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'locking'))
        locking_cards = cursor.fetchall()
        goods_list = [InlineKeyboardButton(i[2] + ' | 库存:{} | 交易中:{}'.format(len(active_cards), len(locking_cards)),
                                           callback_data=str(i[2]))]
        keyboard.append(goods_list)
    conn.close()
    reply_markup = InlineKeyboardMarkup(keyboard)
    if len(goods) == 0:
        query.edit_message_text(text="该分类下暂时还没有商品 主菜单: /start \n")
        return ConversationHandler.END
    else:
        query.edit_message_text(
            text="选择您要购买的商品：\n"
                 "库存：当前可购买数量\n"
                 "交易中：目前其他用户正在购买中，3min不付款将释放订单",
            reply_markup=reply_markup)
        return PRICE


def user_price_filter(update, context):
    query = update.callback_query
    query.answer()
    goods_name = update.callback_query.data
    category_name = context.user_data['category_name']
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name,))
    goods = cursor.fetchone()
    goods_id = goods[0]
    cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'active'))
    active_cards = cursor.fetchall()
    cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'locking'))
    locking_cards = cursor.fetchall()
    conn.close()
    if len(active_cards) == 0 and len(locking_cards) != 0:
        query.edit_message_text(
            text="该商品暂时*无库存*\n"
                 "现在有人*正在交易*，如果超时未支付，该订单将会被释放，届时即可购买\n"
                 "会话已结束，使用 /start 重新发起会话",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    elif len(active_cards) == 0 and len(locking_cards) == 0:
        query.edit_message_text(text="该商品暂时*无库存*，等待补货\n"
                                     "会话已结束，使用 /start 重新发起会话",
                                parse_mode='Markdown', )
        return ConversationHandler.END
    elif len(active_cards) > 0:
        price = goods[3]
        descrip = goods[5]
        context.user_data['descrip'] = descrip
        context.user_data['goods_id'] = goods_id
        context.user_data['goods_name'] = goods_name
        context.user_data['price'] = price
        keyboard = []
        for i in PAYMENT_METHOD:
            payment_method_list = [InlineKeyboardButton(PAYMENT_METHOD[i], callback_data=str(i))]
            keyboard.append(payment_method_list)
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="请选择您的支付方式：",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return CHOOSE_PAYMENT_METHOD


def choose_payment_method(update, context):
    try:
        query = update.callback_query
        query.answer()
        descrip = context.user_data['descrip']
        goods_name = context.user_data['goods_name']
        price = context.user_data['price']
        user_payment_method = update.callback_query.data
        print('用户选择的支付方式为：' + user_payment_method)
        context.user_data['payment_method'] = user_payment_method
        keyboard = [
            [InlineKeyboardButton("提交订单", callback_data=str('提交订单')),
             InlineKeyboardButton("下次一定", callback_data=str('下次一定'))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text='商品名：*{}*\n'
                 '价格：*{}*\n'
                 '介绍：*{}*'.format(goods_name, price, descrip),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return SUBMIT
    except Exception as e:
        print(e)


def submit_trade(update, context):
    print('进入SUBMIT函数')
    query = update.callback_query
    query.answer()
    user = update.callback_query.message.chat
    user_id = user.id
    username = user.username
    chat_id = update.effective_chat.id
    try:
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from trade where user_id=? and status=?", (user_id, 'unpaid'))
        trade_list = cursor.fetchone()
        conn.close()
        if trade_list is None:
            goods_name = context.user_data['goods_name']
            goods_id = context.user_data['goods_id']
            user_payment_method = context.user_data['payment_method']
            category_name = context.user_data['category_name']
            price = context.user_data['price']
            name = category_name + "|" + goods_name
            trade_id = get_trade_id()
            print('商品名：{}，价格：{}，交易ID：{}'.format(name, price, trade_id))
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from goods where id=?", (goods_id,))
            goods_info = cursor.fetchone()
            description = goods_info[5]
            use_way = goods_info[6]
            cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'active'))
            card_info = cursor.fetchone()
            card_id = card_info[0]
            card_content = card_info[3]
            conn.close()
            now_time = int(time.time())
            payment_api = importlib.import_module("getways." + user_payment_method + "." + user_payment_method)
            return_data = payment_api.submit(price, name, trade_id)
            if return_data['status'] == 'Success':
                print('API请求成功')
                conn = sqlite3.connect('faka.sqlite3')
                cursor = conn.cursor()
                cursor.execute("update cards set status=? where id=?", ('locking', card_id,))
                cursor.execute("INSERT INTO trade VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                               (trade_id, goods_id, category_name + "｜" + goods_name, description, use_way, card_id,
                                card_content, user_id, username, now_time, 'unpaid', user_payment_method))
                conn.commit()
                conn.close()
                if return_data['type'] == 'url':
                    pay_url = return_data['data']
                    keyboard = [[InlineKeyboardButton("点击跳转支付", url=pay_url)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    query.edit_message_text(
                        '请在{}s内支付完成，超时支付会导致发货失败！\n'
                        '[点击这里]({})跳转支付，或者点击下方跳转按钮'.format(PAY_TIMEOUT, pay_url),
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    return ConversationHandler.END
                elif return_data['type'] == 'qr_code':
                    qr_code = return_data['data']
                    query.edit_message_text(
                        '请在{}s内支付完成，超时支付会导致发货失败！\n'.format(PAY_TIMEOUT),
                        parse_mode='Markdown',
                    )
                    bot.send_photo(
                        chat_id=chat_id,
                        photo='http://api.qrserver.com/v1/create-qr-code/?data={}&bgcolor=FFFFCB'.format(qr_code)
                    )
                    return ConversationHandler.END
            elif return_data['status'] == 'Failed':
                print(user_payment_method + " 支付接口故障，请前往命令行查看错误信息")
                query.edit_message_text(
                    '订单创建失败：支付接口故障，请联系管理员处理！\n',
                )
                return ConversationHandler.END
        else:
            query.edit_message_text('您存在未支付订单，请支付或等待订单过期后重试！')
            return ConversationHandler.END
    except ModuleNotFoundError:
        print('支付方式不存在，请检查文件名与配置是否一致')
        query.edit_message_text('订单创建失败：支付接口故障，请联系管理员处理！')
        return ConversationHandler.END
    except Exception as e:
        print(e)
        query.edit_message_text('订单创建失败：支付接口故障，请联系管理员处理！')
        return ConversationHandler.END


def cancel_trade(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="记得哦～下次一定")
    return ConversationHandler.END


def trade_filter(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="请回复您需要查询的订单号：")
    return TRADE


def trade_query(update, context):
    trade_id = update.message.text
    user = update.message.from_user
    user_id = user.id
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute('select * from trade where trade_id=? and user_id=?', (trade_id, user_id,))
    trade_list = cursor.fetchone()
    conn.close()
    if trade_list is None:
        update.message.reply_text('订单号有误，请确认后输入！')
        return ConversationHandler.END
    elif trade_list[10] == 'locking':
        goods_name, description, trade_id = trade_list[2], trade_list[3], trade_list[0]
        update.message.reply_text(
            '*订单查询成功*!\n'
            '订单号：`{}`\n'
            '订单状态：*已取消*\n'
            '原因：*逾期未付*'.format(trade_id),
            parse_mode='Markdown',
        )
        return ConversationHandler.END
    elif trade_list[10] == 'paid':
        trade_id, goods_name, description, use_way, card_context = \
            trade_list[0], trade_list[2], trade_list[3], trade_list[4], trade_list[6]
        update.message.reply_text(
            '*订单查询成功*!\n'
            '订单号：`{}`\n'
            '商品：*{}*\n'
            '描述：*{}*\n'
            '卡密内容：`{}`\n'
            '使用方法：*{}*\n'.format(trade_id, goods_name, description, card_context, use_way),
            parse_mode='Markdown',
        )
        return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text('期待再次见到你～')
    return ConversationHandler.END


def get_trade_id():
    now_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(0, 99)
    if random_num <= 10:
        random_num = str(0) + str(random_num)
    unique_num = str(now_time) + str(random_num)
    return unique_num


def timeout(update, context):
    update.message.reply_text('会话超时，期待再次见到你～ /start')
    return ConversationHandler.END


def check_trade():
    while True:
        print('---------------订单轮询开始---------------')
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from trade where status=?", ('unpaid',))
        unpaid_list = cursor.fetchall()
        conn.close()
        for i in unpaid_list:
            now_time = int(time.time())
            trade_id, user_id, creat_time, goods_name, description, use_way, card_context, card_id, payment_method \
                = i[0], i[7], i[9], i[2], i[3], i[4], i[6], i[5], i[11]
            sub_time = now_time - int(creat_time)
            if sub_time >= PAY_TIMEOUT:
                payment_api = importlib.import_module("getways." + payment_method + "." + payment_method)
                payment_api.cancel(trade_id)
                conn = sqlite3.connect('faka.sqlite3')
                cursor = conn.cursor()
                cursor.execute("update trade set status=? where trade_id=?", ('locking', trade_id,))
                cursor.execute("update cards set status=? where id=?", ('active', card_id,))
                conn.commit()
                conn.close()
                bot.send_message(
                    chat_id=user_id,
                    text='很遗憾，订单已关闭\n'
                         '订单号：`{}`\n'
                         '原因：逾期未付\n'.format(trade_id),
                    parse_mode='Markdown',
                )
            else:
                try:
                    payment_api = importlib.import_module("getways." + payment_method + "." + payment_method)
                    rst = payment_api.query(trade_id)
                    if rst == '支付成功':
                        conn = sqlite3.connect('faka.sqlite3')
                        cursor = conn.cursor()
                        cursor.execute("update trade set status=? where trade_id=?", ('paid', trade_id,))
                        cursor.execute("DELETE FROM cards WHERE id=?", (card_id,))
                        conn.commit()
                        conn.close()
                        bot.send_message(
                            chat_id=user_id,
                            text='恭喜！订单支付成功!\n'
                                 '订单号：`{}`\n'
                                 '商品：*{}*\n'
                                 '描述：*{}*\n'
                                 '卡密内容：`{}`\n'
                                 '使用方法：*{}*\n'.format(trade_id, goods_name, description, card_context, use_way),
                            parse_mode='Markdown',
                        )
                except ModuleNotFoundError:
                    print('支付方式不存在，请检查文件名与配置是否一致')
                except Exception as e:
                    print(e)
            time.sleep(3)
        print('---------------订单轮询结束---------------')
        time.sleep(10)


start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            ROUTE: [
                CommandHandler('start', start),
                CallbackQueryHandler(category_filter, pattern='^' + str('购买商品') + '$'),
                CallbackQueryHandler(trade_filter, pattern='^' + str('查询订单') + '$'),
            ],
            CATEGORY: [
                CommandHandler('start', start),
                CallbackQueryHandler(goods_filter, pattern='.*?'),
            ],
            PRICE: [
                CommandHandler('start', start),
                CallbackQueryHandler(user_price_filter, pattern='.*?'),
            ],
            CHOOSE_PAYMENT_METHOD: [
                CommandHandler('start', start),
                CallbackQueryHandler(choose_payment_method, pattern='.*?'),
            ],
            SUBMIT: [
                CommandHandler('start', start),
                CallbackQueryHandler(submit_trade, pattern='^' + str('提交订单') + '$'),
                CallbackQueryHandler(cancel_trade, pattern='^' + str('下次一定') + '$')
            ],
            TRADE: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, trade_query)
            ],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.all, timeout)],
        },
        conversation_timeout=300,
        fallbacks=[CommandHandler('cancel', cancel)]
    )
