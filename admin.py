import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN, ADMIN_ID, ADMIN_COMMAND_START, ADMIN_COMMAND_QUIT
import sqlite3
import time
import os

ADMIN_ROUTE, ADMIN_CATEGORY_ROUTE, CATEGORY_FUNC_EXEC, ADMIN_GOODS_ROUTE, ADMIN_GOODS_STEP1, ADMIN_GOODS_STEP2, \
ADMIN_CARD_ROUTE, ADMIN_TRADE_ROUTE, ADMIN_CARD_STEP1, ADMIN_CARD_STEP2, ADMIN_TRADE_EXEC = range(11)
bot = telegram.Bot(token=TOKEN)


def admin(update, context):
    if is_admin(update, context):
        keyboard = [
            [
                InlineKeyboardButton("分类", callback_data=str('分类')),
                InlineKeyboardButton("商品", callback_data=str('商品')),
                InlineKeyboardButton("卡密", callback_data=str('卡密')),
                InlineKeyboardButton("订单", callback_data=str('订单'))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            '选择您的操作对象：',
            reply_markup=reply_markup
        )
        return ADMIN_ROUTE


def admin_entry_route(update, context):
    query = update.callback_query
    query.answer()
    if update.callback_query.data == '分类':
        keyboard = [
            [
                InlineKeyboardButton("添加分类", callback_data=str('添加分类')),
                InlineKeyboardButton("删除分类", callback_data=str('删除分类')),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择分类指令：",
            reply_markup=reply_markup
        )
        return ADMIN_CATEGORY_ROUTE
    elif update.callback_query.data == '商品':
        keyboard = [
            [
                InlineKeyboardButton("添加商品", callback_data=str('添加商品')),
                InlineKeyboardButton("删除商品", callback_data=str('删除商品')),

            ],
            [
                InlineKeyboardButton("上/下架", callback_data=str('上/下架')),
                InlineKeyboardButton("更改价格", callback_data=str('更改价格')),

            ],
            [
                InlineKeyboardButton("更改描述", callback_data=str('更改描述')),
                InlineKeyboardButton("更改使用方法", callback_data=str('更改使用方法')),
            ],
            [
                InlineKeyboardButton("更改展示优先级", callback_data=str('更改展示优先级'))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择商品指令：",
            reply_markup=reply_markup
        )
        return ADMIN_GOODS_ROUTE
    elif update.callback_query.data == '卡密':
        keyboard = [
            [
                InlineKeyboardButton("添加卡密", callback_data=str('添加卡密')),
                InlineKeyboardButton("导出卡密", callback_data=str('导出卡密')),
                InlineKeyboardButton("删除卡密", callback_data=str('删除卡密')),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择卡密指令：",
            reply_markup=reply_markup
        )
        return ADMIN_CARD_ROUTE
    elif update.callback_query.data == '订单':
        keyboard = [
            [
                InlineKeyboardButton("查询订单", callback_data=str('查询订单')),
                InlineKeyboardButton("重新激活订单", callback_data=str('重新激活订单')),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择分类指令：",
            reply_markup=reply_markup
        )
        return ADMIN_TRADE_ROUTE


def category_func_route(update, context):
    query = update.callback_query
    query.answer()
    if update.callback_query.data == '添加分类':
        context.user_data['func'] = '添加分类'
        query.edit_message_text(text='请输入需要添加的分类名：')
        return CATEGORY_FUNC_EXEC
    elif update.callback_query.data == '删除分类':
        context.user_data['func'] = '删除分类'
        keyboard = []
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from category ORDER BY priority")
        categorys = cursor.fetchall()
        conn.close()
        if len(categorys) == 0:
            query.edit_message_text(text="您还没有添加分类", )
            return ConversationHandler.END
        for i in categorys:
            category_list = []
            category_list.append(InlineKeyboardButton(i[1], callback_data=str(i[1])))
            keyboard.append(category_list)
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择需要删除的分类",
            reply_markup=reply_markup
        )
        return CATEGORY_FUNC_EXEC


def category_func_exec(update, context):
    func = context.user_data['func']
    if func == '添加分类':
        category_name = update.message.text
        context.user_data['category_name'] = category_name
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from category where name=?", (category_name,))
        category_list = cursor.fetchone()
        conn.close()
        if category_list is None:
            context.user_data['func'] = '设置优先级'
            update.message.reply_text('请设置分类展示优先级，数字越小排名越靠前')
            return CATEGORY_FUNC_EXEC
        else:
            update.message.reply_text('分类名不能重复，请检查后重新输入。重启会话 /{}'.format(ADMIN_COMMAND_START))
            return ConversationHandler.END
    elif func == '设置优先级':
        priority = update.message.text
        category_name = context.user_data['category_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO category VALUES (NULL,?,?)", (category_name, priority))
        conn.commit()
        conn.close()
        update.message.reply_text('分类添加成功，会话已退出。重启会话 /{}'.format(ADMIN_COMMAND_START))
        return ConversationHandler.END
    elif func == '删除分类':
        query = update.callback_query
        query.answer()
        category_name = update.callback_query.data
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=?", (category_name,))
        goods_list = cursor.fetchone()
        conn.close()
        if goods_list is None:
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM category WHERE name=?", (category_name,))
            conn.commit()
            conn.close()
            query.edit_message_text(
                text='分类*{}*删除成功！重启会话 /{}'.format(category_name, ADMIN_COMMAND_START),
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        else:
            query.edit_message_text(
                text='分类*{}*下存在商品，请删除该分类下所有商品后重试！重启会话 /{}'.format(category_name, ADMIN_COMMAND_START),
                parse_mode='Markdown'
            )
            return ConversationHandler.END


def goods_func_route(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from category ORDER BY priority")
    categorys = cursor.fetchall()
    conn.close()
    if len(categorys) == 0:
        query.edit_message_text(text='您还没有添加分类。重启会话 /{}'.format(ADMIN_COMMAND_START))
        return ConversationHandler.END
    for i in categorys:
        category_list = []
        category_list.append(InlineKeyboardButton(i[1], callback_data=str(i[1])))
        keyboard.append(category_list)
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query.data == '添加商品':
        context.user_data['func'] = '添加商品'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1
    elif update.callback_query.data == '删除商品':
        context.user_data['func'] = '删除商品'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1
    elif update.callback_query.data == '更改价格':
        context.user_data['func'] = '更改价格'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1
    elif update.callback_query.data == '更改描述':
        context.user_data['func'] = '更改描述'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1
    elif update.callback_query.data == '更改使用方法':
        context.user_data['func'] = '更改使用方法'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1
    elif update.callback_query.data == '上/下架':
        context.user_data['func'] = '上/下架'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1
    elif update.callback_query.data == '更改展示优先级':
        context.user_data['func'] = '更改展示优先级'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1


def goods_func_step1(update, context):
    try:
        query = update.callback_query
        query.answer()
        category_name = update.callback_query.data
        context.user_data['category_name'] = category_name
        func = context.user_data['func']
        keyboard = []
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? ORDER BY priority", (category_name,))
        goods = cursor.fetchall()
        conn.close()
        for i in goods:
            goods_list = [InlineKeyboardButton(i[2], callback_data=str(i[2]))]
            keyboard.append(goods_list)
        reply_markup = InlineKeyboardMarkup(keyboard)
        if func == '添加商品':
            query.edit_message_text(text='请输入需要添加的商品名称：')
            return ADMIN_GOODS_STEP2
        elif func == '删除商品':
            if len(goods) == 0:
                query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
                return ConversationHandler.END
            query.edit_message_text(text="选择需要删除的商品", reply_markup=reply_markup)
            return ADMIN_GOODS_STEP2
        elif func == '更改价格':
            if len(goods) == 0:
                query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
                return ConversationHandler.END
            query.edit_message_text(text="选择需要更改价格的商品", reply_markup=reply_markup)
            return ADMIN_GOODS_STEP2
        elif func == '更改描述':
            if len(goods) == 0:
                query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
                return ConversationHandler.END
            query.edit_message_text(text="选择需要更改描述的商品", reply_markup=reply_markup)
            return ADMIN_GOODS_STEP2
        elif func == '更改使用方法':
            if len(goods) == 0:
                query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
                return ConversationHandler.END
            query.edit_message_text(text="选择需要更改使用方法的商品", reply_markup=reply_markup)
            return ADMIN_GOODS_STEP2
        elif func == '上/下架':
            if len(goods) == 0:
                query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
                return ConversationHandler.END
            query.edit_message_text(text="选择需要更改上架状态的商品", reply_markup=reply_markup)
            return ADMIN_GOODS_STEP2
        elif func == '更改展示优先级':
            if len(goods) == 0:
                query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
                return ConversationHandler.END
            query.edit_message_text(text="选择需要更改展示优先级状态的商品", reply_markup=reply_markup)
            return ADMIN_GOODS_STEP2
    except Exception as e:
        print(e)


def goods_func_step2(update, context):
    query = update.callback_query
    query.answer()
    goods_name = update.callback_query.data
    context.user_data['goods_name'] = goods_name
    category_name = context.user_data['category_name']
    func = context.user_data['func']
    if func == '删除商品':
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name,))
        goods = cursor.fetchone()
        goods_id = goods[0]
        cursor.execute("select * from cards where goods_id=?", (goods_id,))
        card = cursor.fetchone()
        try:
            if card is None:
                cursor.execute("DELETE FROM goods WHERE id=?", (goods_id,))
                conn.commit()
                conn.close()
                query.edit_message_text(text='{}, {}已删除'.format(category_name, goods_name))
                return ConversationHandler.END
            else:
                conn.close()
                query.edit_message_text(text='{}, {} 下存在未删除卡密，请删除该商品全部卡密后重试。重启会话 /{}'.format(
                    category_name, goods_name, ADMIN_COMMAND_START))
                return ConversationHandler.END
        except Exception as e:
            print(e)
    elif func == '更改价格':
        query.edit_message_text(text="您即将修改 {} 下 {} 的价格，输入修改后的价格".format(category_name, goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '更改描述':
        query.edit_message_text(text="您即将修改 {} 下 {} 的描述，输入修改后的描述".format(category_name, goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '更改使用方法':
        query.edit_message_text(text="您即将修改 {} 下 {} 的使用方法，输入修改后的使用方法".format(category_name, goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '上/下架':
        keyboard = [
            [InlineKeyboardButton("上架", callback_data=str('上架')),
             InlineKeyboardButton("下架", callback_data=str('下架'))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="您即将修改 {} 下 {} 的上下架状态，请选择：".format(category_name, goods_name),
                                reply_markup=reply_markup)
        return ADMIN_GOODS_STEP2
    elif func == '更改展示优先级':
        query.edit_message_text(text="您即将修改 {} 下 {} 的展示优先级，输入修改后的优先级".format(category_name, goods_name))
        return ADMIN_GOODS_STEP2


def goods_func_exec(update, context):
    category_name = context.user_data['category_name']
    func = context.user_data['func']
    if func == '添加商品':
        goods_name = update.message.text
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name))
        goods_list = cursor.fetchone()
        conn.close()
        if goods_list is None:
            context.user_data['goods_name'] = goods_name
            context.user_data['func'] = '设置价格'
            update.message.reply_text('请为 {} 设置价格：'.format(goods_name))
            return ADMIN_GOODS_STEP2
        else:
            update.message.reply_text(
                '分类 {} 下存在同名商品 {}，请检查后重试。重启会话 /{}'.format(category_name, goods_name, ADMIN_COMMAND_START))
            return ConversationHandler.END
    elif func == '设置价格':
        goods_price = update.message.text
        goods_name = context.user_data['goods_name']
        context.user_data['goods_price'] = goods_price
        context.user_data['func'] = '设置描述'
        update.message.reply_text('请为 {} 设置描述：'.format(goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '设置描述':
        description = update.message.text
        goods_name = context.user_data['goods_name']
        context.user_data['description'] = description
        context.user_data['func'] = '设置使用方法'
        update.message.reply_text('请为 {} 设置使用方法：'.format(goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '设置使用方法':
        use_way = update.message.text
        goods_name = context.user_data['goods_name']
        context.user_data['use_way'] = use_way
        context.user_data['func'] = '设置优先级'
        update.message.reply_text('请为 {} 设置展示优先级，数字越小越靠前：'.format(goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '设置优先级':
        try:
            priority = update.message.text
            use_way = context.user_data['use_way']
            goods_name = context.user_data['goods_name']
            goods_price = context.user_data['goods_price']
            description = context.user_data['description']
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO goods VALUES (NULL,?,?,?,?,?,?,?)",
                           (category_name, goods_name, goods_price, 'active', description, use_way, priority))
            conn.commit()
            conn.close()
            update.message.reply_text('商品 {} 添加成功 重启会话 /{}'.format(goods_name, ADMIN_COMMAND_START))
            return ConversationHandler.END
        except Exception as e:
            print(e)
    elif func == '更改价格':
        price = update.message.text
        goods_name = context.user_data['goods_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update goods set price=? where category_name=? and name=?",
                       (price, category_name, goods_name))
        conn.commit()
        conn.close()
        update.message.reply_text(' {} 下 {} 价格更新成功，修改后的价格为：{} 重启会话 /{}'.format(
            category_name, goods_name, price, ADMIN_COMMAND_START))
        return ConversationHandler.END
    elif func == '更改描述':
        discription = update.message.text
        goods_name = context.user_data['goods_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update goods set description=? where category_name=? and name=?",
                       (discription, category_name, goods_name))
        conn.commit()
        conn.close()
        update.message.reply_text(' {} 下 {} 描述更新成功，修改后的描述为：{}'.format(category_name, goods_name, discription))
        return ConversationHandler.END
    elif func == '更改使用方法':
        use_way = update.message.text
        goods_name = context.user_data['goods_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update goods set use_way=? where category_name=? and name=?",
                       (use_way, category_name, goods_name))
        conn.commit()
        conn.close()
        update.message.reply_text(' {} 下 {} 使用方法更新成功，修改后的使用方法为：{}'.format(category_name, goods_name, use_way))
        return ConversationHandler.END
    elif func == '更改展示优先级':
        priority = update.message.text
        goods_name = context.user_data['goods_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update goods set priority=? where category_name=? and name=?",
                       (priority, category_name, goods_name))
        conn.commit()
        conn.close()
        update.message.reply_text(' {} 下 {} 使用方法更新成功，修改后的优先级为：{}'.format(category_name, goods_name, priority))
        return ConversationHandler.END


def goods_func_set_status(update, context):
    query = update.callback_query
    query.answer()
    goods_status = update.callback_query.data
    category_name = context.user_data['category_name']
    goods_name = context.user_data['goods_name']
    func = context.user_data['func']
    if func == '上/下架':
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name,))
        goods = cursor.fetchone()
        now_goods_status = goods[4]
        if goods_status == '上架':
            if now_goods_status == 'active':
                query.edit_message_text('分类 {} 下 {} 的状态已经是上架状态，无需变动。重启会话 /{}'.format(
                    category_name, goods_name, ADMIN_COMMAND_START))
                conn.close()
                return ConversationHandler.END
            else:
                cursor.execute("update goods set status=? where category_name=? and name=?",
                               ('active', category_name, goods_name,))
                conn.commit()
                conn.close()
                query.edit_message_text('已将分类 {} 下 {} 的状态修改为上架'.format(category_name, goods_name))
                return ConversationHandler.END
        else:
            if now_goods_status == 'deactive':
                query.edit_message_text('分类 {} 下 {} 的状态已经是下架状态，无需变动。重启会话 /{}'.format(
                    category_name, goods_name, ADMIN_COMMAND_START))
                conn.close()
                return ConversationHandler.END
            else:
                cursor.execute("update goods set status=? where category_name=? and name=?",
                               ('deactive', category_name, goods_name,))
                conn.commit()
                conn.close()
                query.edit_message_text('已将分类 {} 下 {} 的状态修改为下架'.format(category_name, goods_name))
                return ConversationHandler.END


def card_func_route(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from category ORDER BY priority")
    categorys = cursor.fetchall()
    conn.close()
    if len(categorys) == 0:
        query.edit_message_text(text='您还没有添加分类。重启会话 /{}'.format(ADMIN_COMMAND_START))
        return ConversationHandler.END
    for i in categorys:
        category_list = []
        category_list.append(InlineKeyboardButton(i[1], callback_data=str(i[1])))
        keyboard.append(category_list)
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query.data == '添加卡密':
        context.user_data['func'] = '添加卡密'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_CARD_STEP1
    elif update.callback_query.data == '删除卡密':
        context.user_data['func'] = '删除卡密'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_CARD_STEP1
    elif update.callback_query.data == '导出卡密':
        context.user_data['func'] = '导出卡密'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_CARD_STEP1


def card_func_step1(update, context):
    try:
        query = update.callback_query
        query.answer()
        category_name = update.callback_query.data
        context.user_data['category_name'] = category_name
        func = context.user_data['func']
        keyboard = []
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? ORDER BY priority", (category_name,))
        goods = cursor.fetchall()
        conn.close()
        if len(goods) == 0:
            query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
            return ConversationHandler.END
        for i in goods:
            goods_list = [InlineKeyboardButton(i[2], callback_data=str(i[2]))]
            keyboard.append(goods_list)
        reply_markup = InlineKeyboardMarkup(keyboard)
        if func == '添加卡密':
            query.edit_message_text(text="选择需要添加卡密的商品", reply_markup=reply_markup)
            return ADMIN_CARD_STEP2
        elif func == '删除卡密':
            query.edit_message_text(
                text="选择需要删除卡密的商品\n"
                     "*注意：点击后卡密直接删除，稍后会将备份的卡密通过窗口发送给您!!!*",
                parse_mode='Markdown',
                reply_markup=reply_markup)
            return ADMIN_CARD_STEP2
        elif func == '导出卡密':
            query.edit_message_text(text="选择需要导出卡密的商品", reply_markup=reply_markup)
            return ADMIN_CARD_STEP2
    except Exception as e:
        print(e)


def card_func_step2(update, context):
    try:
        query = update.callback_query
        query.answer()
        goods_name = update.callback_query.data
        context.user_data['goods_name'] = goods_name
        category_name = context.user_data['category_name']
        func = context.user_data['func']
        if func == '添加卡密':
            query.edit_message_text(
                text='请发送文件名为: *分类名|商品名.txt* 的TXT文件\n'
                     '文件内容为卡密，一行一个\n',
                parse_mode='Markdown', )
            return ADMIN_CARD_STEP2
        elif func == '删除卡密':
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name))
            goods = cursor.fetchone()
            goods_id = goods[0]
            cursor.execute("select * from cards where goods_id=?", (goods_id,))
            cards_list = cursor.fetchall()
            if len(cards_list) == 0:
                conn.close()
                query.edit_message_text(text=" {} 下 {} 不存在卡密".format(category_name, goods_name))
                return ConversationHandler.END
            else:
                new_file = open('./card/导出卡密｜{}｜{}.txt'.format(category_name, goods_name), 'w')
                for card in cards_list:
                    context = card[3]
                    new_file.write(context + '\n')
                new_file.close()
                cursor.execute("delete from cards where goods_id=?", (goods_id,))
                conn.commit()
                conn.close()
                chat_id = query.message.chat.id
                bot.send_document(chat_id=chat_id, document=open(
                    './card/导出卡密｜{}｜{}.txt'.format(category_name, goods_name), 'rb'))
                os.remove('./card/导出卡密｜{}｜{}.txt'.format(category_name, goods_name))
                query.edit_message_text(text="分类 {} 下 {} 卡密已全部删除".format(category_name, goods_name))
                return ConversationHandler.END
        elif func == '导出卡密':
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name))
            goods = cursor.fetchone()
            goods_id = goods[0]
            cursor.execute("select * from cards where goods_id=?", (goods_id,))
            cards_list = cursor.fetchall()
            conn.close()
            if len(cards_list) == 0:
                query.edit_message_text(text=" {} 下 {} 不存在卡密".format(category_name, goods_name))
                return ConversationHandler.END
            else:
                new_file = open('./card/导出卡密｜{}｜{}.txt'.format(category_name, goods_name), 'w')
                for card in cards_list:
                    context = card[3]
                    new_file.write(context + '\n')
                new_file.close()
                chat_id = query.message.chat.id
                bot.send_document(chat_id=chat_id, document=open(
                    './card/导出卡密｜{}｜{}.txt'.format(category_name, goods_name), 'rb'))
                os.remove('./card/导出卡密｜{}｜{}.txt'.format(category_name, goods_name))
                query.edit_message_text(text="卡密已经导出")
                return ConversationHandler.END
    except Exception as e:
        print(e)


def card_add_exec(update, context):
    try:
        category_name = context.user_data['category_name']
        goods_name = context.user_data['goods_name']
        file_id = update.message.document.file_id
        new_file = bot.get_file(file_id)
        file_name = update.message.document.file_name
        new_file.download(custom_path='./card/{}'.format(file_name))
        try:
            split_file_name = file_name.split('.')[0]
            user_file_category_name = split_file_name.split('｜')[0]
            user_file_goods_name = split_file_name.split('｜')[1]
        except Exception as e:
            update.message.reply_text('文件名有误，请检查后重新发送！重启会话 /{}'.format(ADMIN_COMMAND_START))
            return ConversationHandler.END
        if user_file_category_name != category_name or user_file_goods_name != goods_name:
            update.message.reply_text('文件名有误，请检查后重新发送！重启会话 /{}'.format(ADMIN_COMMAND_START))
            return ConversationHandler.END
        else:
            f = open("./card/{}".format(file_name))
            card_list = []
            while True:
                lines = f.readlines(10000)
                if not lines:
                    break
                for line in lines:
                    card_list.append(line)
            new_card_list = []
            for card in card_list[:-1]:
                new_card_list.append(card[:-1])
            new_card_list.append(card_list[-1])
            f.close()
            card_len = len(new_card_list)
            os.remove('./card/{}'.format(file_name))
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name))
            goods = cursor.fetchone()
            goods_id = goods[0]
            for i in new_card_list:
                cursor.execute("INSERT INTO cards VALUES (NULL,?,?,?)", ('active', goods_id, i))
            conn.commit()
            conn.close()
            update.message.reply_text('卡密添加成功，添加的卡密数量为：{}'.format(card_len))
            return ConversationHandler.END
    except Exception as e:
        print(e)


def trade_func_route(update, context):
    query = update.callback_query
    query.answer()
    if update.callback_query.data == '查询订单':
        context.user_data['func'] = '查询订单'
        query.edit_message_text(text="请回复您需要查询的订单号：")
        return ADMIN_TRADE_EXEC
    elif update.callback_query.data == '重新激活订单':
        context.user_data['func'] = '重新激活订单'
        query.edit_message_text(text="请回复您需要重新激活的订单号：")
        return ADMIN_TRADE_EXEC


def itimeout(update, context):
    update.message.reply_text('会话超时，期待再次见到你～ /{}'.format(ADMIN_COMMAND_START))
    return ConversationHandler.END


def admin_trade_func_exec(update, context):
    try:
        trade_id = update.message.text
        func = context.user_data['func']
        if func == '查询订单':
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute('select * from trade where trade_id=?', (trade_id,))
            trade_list = cursor.fetchone()
            conn.close()
            if trade_list is None:
                update.message.reply_text('订单号有误，请确认后输入！')
                return ConversationHandler.END
            else:
                if trade_list[10] == 'paid':
                    status = '已支付'
                elif trade_list[10] == 'locking':
                    status = '已锁定'
                elif trade_list[10] == 'unpaid':
                    status = '未支付'
                goods_name = trade_list[2]
                description = trade_list[3]
                username = trade_list[8]
                card_context = trade_list[6]
                use_way = trade_list[4]
                trade_id = trade_list[0]
                update.message.reply_text(
                    '*订单查询成功*!\n'
                    '订单号：`{}`\n'
                    '订单状态：{}\n'
                    '下单用户：@{}\n'
                    '卡密内容：`{}`\n'
                    '描述：*{}*\n'
                    '使用方法：*{}*'.format(trade_id, status, username, card_context, description, use_way),
                    parse_mode='Markdown',
                )
                return ConversationHandler.END
        elif func == '重新激活订单':
            now_time = int(time.time())
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from trade where trade_id=?", (trade_id,))
            trade = cursor.fetchone()
            card_content = trade[6]
            cursor.execute("select * from trade where card_contents=? and status=?", (card_content, 'paid'))
            paid_trade = cursor.fetchone()
            if paid_trade is not None:
                update.message.reply_text('该卡密已被其他用户抢购，无法重新激活轮询！')
                return ConversationHandler.END
            else:
                cursor.execute('update trade set creat_time=? where trade_id=?', (now_time, trade_id,))
                cursor.execute('update trade set status=? where trade_id=?', ('unpaid', trade_id,))
                conn.commit()
                conn.close()
                update.message.reply_text('该订单已经重新放入轮询队列')
                return ConversationHandler.END
    except Exception as e:
        print(e)


def is_admin(update, context):
    if update.message.from_user.id in ADMIN_ID:
        return True
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='*非管理员，无权操作*',
            parse_mode='Markdown'
        )
        return False


def icancel(update, context):
    update.message.reply_text('期待再次见到你～ /{}'.format(ADMIN_COMMAND_START))
    return ConversationHandler.END


admin_handler = ConversationHandler(
        entry_points=[CommandHandler(ADMIN_COMMAND_START, admin)],

        states={
            ADMIN_ROUTE: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CallbackQueryHandler(admin_entry_route, pattern='^' + str('分类') + '$'),
                CallbackQueryHandler(admin_entry_route, pattern='^' + str('商品') + '$'),
                CallbackQueryHandler(admin_entry_route, pattern='^' + str('卡密') + '$'),
                CallbackQueryHandler(admin_entry_route, pattern='^' + str('订单') + '$'),
            ],
            ADMIN_CATEGORY_ROUTE: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CallbackQueryHandler(category_func_route, pattern='^' + '(添加|删除)分类' + '$'),
            ],
            CATEGORY_FUNC_EXEC: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CommandHandler(ADMIN_COMMAND_QUIT, icancel),
                MessageHandler(Filters.text, category_func_exec),
                CallbackQueryHandler(category_func_exec, pattern='.*?')
            ],
            ADMIN_GOODS_ROUTE: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CallbackQueryHandler(goods_func_route, pattern='^' + '(添加商品|删除商品|上/下架|更改价格|更改描述|更改使用方法|更改展示优先级)' + '$'),
            ],
            ADMIN_GOODS_STEP1: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CallbackQueryHandler(goods_func_step1, pattern='.*?')
            ],
            ADMIN_GOODS_STEP2: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CommandHandler(ADMIN_COMMAND_QUIT, icancel),
                MessageHandler(Filters.text, goods_func_exec),
                CallbackQueryHandler(goods_func_set_status, pattern='^' + '(上架|下架)' + '$'),
                CallbackQueryHandler(goods_func_step2, pattern='.*?')
            ],
            ADMIN_CARD_ROUTE: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CallbackQueryHandler(card_func_route, pattern='^' + '(添加卡密|删除卡密|导出卡密)' + '$'),
            ],
            ADMIN_CARD_STEP1: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CommandHandler(ADMIN_COMMAND_QUIT, icancel),
                CallbackQueryHandler(card_func_step1, pattern='.*?')
            ],
            ADMIN_CARD_STEP2: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CommandHandler(ADMIN_COMMAND_QUIT, icancel),
                MessageHandler(Filters.document, card_add_exec),
                CallbackQueryHandler(card_func_step2, pattern='.*?')
            ],
            ADMIN_TRADE_ROUTE: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                CallbackQueryHandler(trade_func_route, pattern='^' + '(查询订单|重新激活订单)' + '$'),
            ],
            ADMIN_TRADE_EXEC: [
                CommandHandler(ADMIN_COMMAND_START, admin),
                MessageHandler(Filters.text, admin_trade_func_exec)
            ],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.all, itimeout)],
        },
        conversation_timeout=300,
        fallbacks=[CommandHandler(ADMIN_COMMAND_QUIT, icancel)]
    )


