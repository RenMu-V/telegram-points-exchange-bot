# main.py
import configparser
import logging
import random
import asyncio
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters

# --- 日志配置 ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 全局变量 ---
# 状态定义
SELECTING_ACTION, SELECTING_SOURCE, SELECTING_TARGET, CONFIRMING = range(4)

# 配置变量 (将在启动时从 config.ini 加载)
BOT_TOKEN = None
EXCHANGE_RATE = None
ADMIN_IDS = []
NOTIFICATION_GROUP_IDS = []
DATABASE_A_CONFIG = {}
DATABASE_B_CONFIG = {}

# ==============================================================================
# 🎯 数据库操作函数 (泛化版本)
# ==============================================================================

async def get_user_points_a(user_id: int) -> int:
    """从数据库A获取用户积分"""
    # 这里应该是你的数据库查询逻辑
    # 示例: return await db_a_query("SELECT points FROM users WHERE user_id = ?", (user_id,))
    # 为了演示，返回一个模拟值
    return 1000

async def update_user_points_a(user_id: int, points_to_deduct: int) -> bool:
    """更新数据库A中的用户积分"""
    # 这里应该是你的数据库更新逻辑
    # 示例: await db_a_execute("UPDATE users SET points = points - ? WHERE user_id = ? AND points >= ?", (points_to_deduct, user_id, points_to_deduct))
    # 为了演示，总是返回成功
    return True

async def add_user_points_b(user_id: int, points_to_add: int) -> bool:
    """向数据库B添加用户积分"""
    # 这里应该是你的数据库更新逻辑
    # 示例: await db_b_execute("INSERT INTO transactions (user_id, points) VALUES (?, ?)", (user_id, points_to_add))
    # 为了演示，总是返回成功
    return True

# ==============================================================================
# 🎯 通知函数 (支持多群组)
# ==============================================================================
async def send_group_notification(context: ContextTypes.DEFAULT_TYPE, user_id: int, amount: int, amount_added: int) -> None:
    """向配置的所有群组发送有趣的兑换通知"""
    if not NOTIFICATION_GROUP_IDS:
        return

    # 尝试获取用户昵称并生成可点击链接
    user_link = f'<a href="tg://user?id={user_id}">用户 {user_id}</a>'
    try:
        chat = await context.bot.get_chat(chat_id=user_id)
        if chat.first_name:
            display_name = chat.first_name
            if chat.last_name:
                display_name += f" {chat.last_name}"
            user_link = f'<a href="tg://user?id={user_id}">{display_name}</a>'
    except Exception as e:
        logger.warning(f"无法获取用户 {user_id} 的昵称信息: {e}")

    # 有趣的文案库
    congratulations = [
        f"🎉 恭喜！又一位老板成功兑换！{user_link} 将 <code>{amount}</code> 积分A瞬间变成了 <code>{amount_added}</code> 积分B，太给力了！",
        f"🥳 哇塞！{user_link} 完成了一次丝滑小连招！<code>{amount}</code> 积分A → <code>{amount_added}</code> 积分B，感谢支持！",
        f"💰 叮！您的账户到账 <code>{amount_added}</code> 积分B！感谢 {user_link} 的慷慨投喂，服务器又能续费一秒了！",
        f"🚀 兑换成功！{user_link} 巧妙地将 <code>{amount}</code> 积分A打包成 <code>{amount_added}</code> 积分B，发送到您的账户！感谢您的支持，爱您哟！💖",
        f"✨ 又一笔成功的交易！{user_link} 是个理财小能手！<code>{amount}</code> 积分A → <code>{amount_added}</code> 积分B，收益满满！",
        f"🍬➡️🍯 美妙的转化发生了！{user_link} 用 <code>{amount}</code> 积分A换来了 <code>{amount_added}</code> 积分B，生活甜甜蜜蜜！",
        f"🧪 炼金术大师 {user_link} 出手了！<code>{amount}</code> 积分A经过神秘仪式，成功转化为 <code>{amount_added}</code> 积分B！太神奇了！",
        f"🎮 任务完成！{user_link} 成功提交了 <code>{amount}</code> 积分A的“任务奖励”，兑换了 <code>{amount_added}</code> 积分B的“经验包”！",
        f"👨‍🍳 大厨 {user_link} 正在烹饪！主料 <code>{amount}</code> 积分A，经过精心调配，出锅了 <code>{amount_added}</code> 积分B的美味佳肴！",
        f"🛸 UFO警报！{user_link} 注入了 <code>{amount}</code> 单位的“燃料A”，飞船成功跃迁，获得了 <code>{amount_added}</code> 单位的“能量B”！",
        f"📈 投资高手 {user_link} 操作！将 <code>{amount}</code> 积分A的“资产”进行重组，成功升值到 <code>{amount_added}</code> 积分B！眼光独到！",
    ]
    
    message = random.choice(congratulations)
    
    for group_id in NOTIFICATION_GROUP_IDS:
        try:
            await context.bot.send_message(chat_id=group_id, text=message, parse_mode='HTML')
            logger.info(f"成功向群组 {group_id} 发送通知。")
        except Exception as e:
            logger.error(f"向群组 {group_id} 发送通知失败: {e}")

# ==============================================================================
# 🎯 Bot 交互函数
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """启动命令，显示主菜单"""
    keyboard = [
        [InlineKeyboardButton("💱 积分兑换", callback_data='exchange')],
        [InlineKeyboardButton("ℹ️ 帮助", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 欢迎使用积分兑换Bot！\n\n请选择您需要的服务：",
        reply_markup=reply_markup
    )
    return SELECTING_ACTION

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """处理按钮回调"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'exchange':
        await exchange_start(update, context)
        return SELECTING_SOURCE
    elif query.data == 'help':
        await show_help(update, context)
        return SELECTING_ACTION
    elif query.data.startswith('confirm_'):
        await process_exchange(update, context)
        return ConversationHandler.END
    elif query.data == 'cancel':
        await query.edit_message_text("❌ 操作已取消。")
        return ConversationHandler.END
    
    return SELECTING_ACTION

async def exchange_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始兑换流程"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # 获取用户当前积分A
    points_a = await get_user_points_a(user_id)
    
    keyboard = [
        [InlineKeyboardButton(f"100 积分A → 20 积分B", callback_data='exchange_100')],
        [InlineKeyboardButton(f"200 积分A → 40 积分B", callback_data='exchange_200')],
        [InlineKeyboardButton(f"500 积分A → 100 积分B", callback_data='exchange_500')],
        [InlineKeyboardButton("❌ 取消", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💱 积分兑换\n\n"
        f"您当前拥有: <b>{points_a}</b> 积分A\n"
        f"兑换比例: 1 积分A = {EXCHANGE_RATE} 积分B\n\n"
        f"请选择要兑换的数量：",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def process_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理兑换逻辑"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # 解析兑换数量
    amount_str = query.data.split('_')[1]
    amount = int(amount_str)
    amount_added = amount * EXCHANGE_RATE
    
    try:
        # 检查积分A是否足够
        current_points_a = await get_user_points_a(user_id)
        if current_points_a < amount:
            await query.edit_message_text(
                f"❌ 兑换失败！\n\n"
                f"您的积分A不足。\n"
                f"需要: {amount} 积分A\n"
                f"当前: {current_points_a} 积分A"
            )
            return
        
        # 执行数据库操作
        success_a = await update_user_points_a(user_id, amount)
        if not success_a:
            raise Exception("更新积分A失败")
            
        success_b = await add_user_points_b(user_id, amount_added)
        if not success_b:
            raise Exception("添加积分B失败")
        
        # 兑换成功，发送通知
        await send_group_notification(context, user_id, amount, amount_added)
        
        await query.edit_message_text(
            f"✅ 兑换成功！\n\n"
            f"您已成功将 <b>{amount}</b> 积分A兑换为 <b>{amount_added}</b> 积分B。\n"
            f"感谢您的支持！",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"用户 {user_id} 兑换时发生错误: {e}")
        await query.edit_message_text(
            f"❌ 兑换失败！\n\n"
            f"系统发生错误，请联系管理员。\n"
            f"错误信息: {str(e)}"
        )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示帮助信息"""
    query = update.callback_query
    help_text = (
        "ℹ️ <b>帮助信息</b>\n\n"
        f"<b>兑换比例:</b> 1 积分A = {EXCHANGE_RATE} 积分B\n\n"
        "<b>使用说明:</b>\n"
        "1. 点击「积分兑换」按钮\n"
        "2. 选择要兑换的数量\n"
        "3. 确认兑换\n\n"
        "<b>注意事项:</b>\n"
        "• 兑换操作不可撤销\n"
        "• 请确保积分A充足\n"
        "• 如有问题请联系管理员"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='HTML')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """取消操作"""
    await update.message.reply_text("❌ 操作已取消。")
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理错误"""
    logger.error('Exception while handling an update:', exc_info=context.error)

# ==============================================================================
# 🎯 主函数
# ==============================================================================

def main():
    """启动Bot"""
    global BOT_TOKEN, EXCHANGE_RATE, ADMIN_IDS, NOTIFICATION_GROUP_IDS
    
    # --- 配置加载 ---
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    try:
        BOT_TOKEN = config['telegram']['token']
        EXCHANGE_RATE = int(config['settings']['exchange_rate'])
        ADMIN_IDS = [int(uid.strip()) for uid in config['admin']['user_ids'].split(',') if uid.strip()]
        
        # 加载多个通知群组ID
        NOTIFICATION_GROUP_IDS = []
        if 'notification' in config and 'group_ids' in config['notification']:
            ids_str = config['notification']['group_ids']
            NOTIFICATION_GROUP_IDS = [int(id.strip()) for id in ids_str.split(',') if id.strip()]
            
    except KeyError as e:
        print(f"❌ 配置文件 config.ini 中缺少必要的项: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        sys.exit(1)
    
    # 创建应用
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 设置对话处理器
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [CallbackQueryHandler(button_callback)],
            SELECTING_SOURCE: [CallbackQueryHandler(button_callback)],
            SELECTING_TARGET: [CallbackQueryHandler(button_callback)],
            CONFIRMING: [CallbackQueryHandler(button_callback)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CallbackQueryHandler(cancel, pattern='^cancel$')],
        per_message=False,
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    # 启动Bot
    logger.info("🚀 积分兑换 Bot 正在启动...")
    application.run_polling()

if __name__ == '__main__':
    main()
