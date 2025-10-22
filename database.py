import aiomysql
import configparser
from typing import Optional, Tuple

# 全局变量用于存储数据库连接池
source_pool = None  # 源积分数据库连接池
target_pool = None  # 目标积分数据库连接池

async def create_db_pools(config_file: str = 'config.ini'):
    """读取配置并创建数据库连接池"""
    global source_pool, target_pool
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')

    try:
        # 创建源积分数据库连接池
        source_pool = await aiomysql.create_pool(
            host=config.get('database_source', 'host'),
            port=config.getint('database_source', 'port'),
            user=config.get('database_source', 'user'),
            password=config.get('database_source', 'password'),
            db=config.get('database_source', 'database'),
            autocommit=True
        )
        
        # 创建目标积分数据库连接池
        target_pool = await aiomysql.create_pool(
            host=config.get('database_target', 'host'),
            port=config.getint('database_target', 'port'),
            user=config.get('database_target', 'user'),
            password=config.get('database_target', 'password'),
            db=config.get('database_target', 'database'),
            autocommit=True
        )
        print("数据库连接池创建成功！")
    except Exception as e:
        print(f"创建数据库连接池失败: {e}")
        raise

async def get_user_points(pool: aiomysql.Pool, tg_id: int) -> Optional[int]:
    """从指定数据库连接池中获取用户的积分"""
    if not pool:
        return None
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # 使用参数化查询防止SQL注入
            # 注意：请根据实际数据库表结构调整查询语句
            await cursor.execute("SELECT points FROM users WHERE tg_id = %s", (tg_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

async def perform_exchange(tg_id: int, source_points_to_exchange: int, rate: int) -> Tuple[bool, str]:
    """
    执行积分兑换操作
    :param tg_id: 用户的 Telegram ID
    :param source_points_to_exchange: 要兑换的源积分数量
    :param rate: 兑换比例 (多少源积分兑换1个目标积分)
    :return: (是否成功, 消息)
    """
    global source_pool, target_pool
    
    # 1. 检查用户在两个服是否存在
    source_points = await get_user_points(source_pool, tg_id)
    target_points = await get_user_points(target_pool, tg_id)

    if source_points is None:
        return False, "❌ 您尚未在源服务注册或绑定TG账号。"
    if target_points is None:
        return False, "❌ 您尚未在目标服务注册或绑定TG账号。"

    # 2. 检查源积分是否足够
    if source_points < source_points_to_exchange:
        return False, f"❌ 您的源积分不足。当前积分: {source_points}"

    # 3. 计算可兑换的目标积分
    target_points_to_add = source_points_to_exchange // rate
    if target_points_to_add == 0:
        return False, f"❌ 兑换数量不足。至少需要 {rate} 源积分才能兑换 1 目标积分。"

    # 4. 执行数据库操作 (先扣后增)
    async with source_pool.acquire() as source_conn:
        async with source_conn.cursor() as source_cursor:
            try:
                # 开始事务
                await source_conn.begin()
                
                # 扣除源积分
                await source_cursor.execute(
                    "UPDATE users SET points = points - %s WHERE tg_id = %s",
                    (source_points_to_exchange, tg_id)
                )
                if source_cursor.rowcount == 0:
                    raise Exception("源服务更新失败，可能用户不存在。")
                
                # 提交事务
                await source_conn.commit()
                print(f"用户 {tg_id} 扣除 {source_points_to_exchange} 源积分成功。")
            except Exception as e:
                await source_conn.rollback()
                print(f"用户 {tg_id} 扣除源积分失败: {e}")
                return False, "❌ 兑换失败：扣除源积分时发生错误，请联系管理员。"

    # 如果扣除成功，再增加目标积分
    async with target_pool.acquire() as target_conn:
        async with target_conn.cursor() as target_cursor:
            try:
                await target_conn.begin()
                
                await target_cursor.execute(
                    "UPDATE users SET points = points + %s WHERE tg_id = %s",
                    (target_points_to_add, tg_id)
                )
                if target_cursor.rowcount == 0:
                    raise Exception("目标服务更新失败，可能用户不存在。")
                
                await target_conn.commit()
                print(f"用户 {tg_id} 增加 {target_points_to_add} 目标积分成功。")
            except Exception as e:
                await target_conn.rollback()
                print(f"用户 {tg_id} 增加目标积分失败: {e}")
                # **重要**: 如果增加失败，需要手动把扣掉的源积分加回去！
                async with source_pool.acquire() as source_conn_rollback:
                    async with source_conn_rollback.cursor() as source_cursor_rollback:
                        await source_cursor_rollback.execute(
                            "UPDATE users SET points = points + %s WHERE tg_id = %s",
                            (source_points_to_exchange, tg_id)
                        )
                        print(f"已为用户 {tg_id} 回滚 {source_points_to_exchange} 源积分。")
                return False, "❌ 兑换失败：增加目标积分时发生错误，已为您回滚源积分，请重试或联系管理员。"

    return True, f"✅ 兑换成功！\n- 扣除源积分: {source_points_to_exchange}\n- 增加目标积分: {target_points_to_add}"

async def close_db_pools():
    """关闭数据库连接池"""
    global source_pool, target_pool
    if source_pool:
        source_pool.close()
        await source_pool.wait_closed()
    if target_pool:
        target_pool.close()
        await target_pool.wait_closed()
    print("数据库连接池已关闭。")

# 配置文件示例 (config.example.ini)
"""
[database_source]
host = localhost
port = 3306
user = your_db_user
password = your_db_password
database = your_source_database

[database_target]
host = localhost
port = 3306
user = your_db_user
password = your_db_password
database = your_target_database
"""
