# test_db.py
import asyncio
import aiomysql
import configparser
import sys

async def test_connection(config_section: str = 'database_source', db_name: str = '源数据库'):
    """
    测试数据库连接
    :param config_section: 配置文件中的节名
    :param db_name: 数据库显示名称
    """
    print(f"--- 开始{db_name}连接测试 ---")
    config = configparser.ConfigParser()
    try:
        config.read('config.ini', encoding='utf-8')
        db_config = config[config_section]
    except Exception as e:
        print(f"❌ 读取 config.ini 失败: {e}")
        return

    try:
        print(f"正在尝试连接到{db_name} {db_config['host']}:{db_config['port']}...")
        conn = await aiomysql.connect(
            host=db_config['host'],
            port=int(db_config['port']),
            user=db_config['user'],
            password=db_config['password'],
            db=db_config['database'],
        )
        print(f"✅ {db_name}连接成功！数据库可达，权限也正确。")
        
        # 可选：执行一个简单查询来验证数据库可操作性
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT 1")
            result = await cursor.fetchone()
            if result:
                print(f"✅ {db_name}查询测试通过，数据库完全可用。")
        
        conn.close()
    except aiomysql.OperationalError as e:
        code = e.args[0]
        msg = e.args[1]
        if code == 2003:
            print(f"❌ {db_name}连接失败 (错误代码 {code}): {msg}")
            print("这通常是网络或防火墙问题。请检查：")
            print("1. 数据库服务器地址和端口是否正确")
            print("2. 防火墙是否允许从当前服务器访问数据库")
            print("3. 云服务器的安全组规则是否正确配置")
        elif code == 1045:
            print(f"❌ {db_name}连接失败 (错误代码 {code}): {msg}")
            print("网络已通，但认证失败。请检查：")
            print("1. 数据库用户名是否正确")
            print("2. 数据库密码是否正确")
            print("3. 用户是否有访问该数据库的权限")
        elif code == 1049:
            print(f"❌ {db_name}连接失败 (错误代码 {code}): {msg}")
            print("数据库不存在。请检查数据库名称是否正确。")
        else:
            print(f"❌ {db_name}发生未知数据库错误: {e}")
    except Exception as e:
        print(f"❌ {db_name}发生未知错误: {e}")

async def test_all_connections():
    """测试所有配置的数据库连接"""
    config = configparser.ConfigParser()
    try:
        config.read('config.ini', encoding='utf-8')
        
        # 测试源数据库
        if 'database_source' in config:
            await test_connection('database_source', '源数据库')
        else:
            print("⚠️ 未找到源数据库配置 [database_source]")
        
        print("\n" + "="*50 + "\n")
        
        # 测试目标数据库
        if 'database_target' in config:
            await test_connection('database_target', '目标数据库')
        else:
            print("⚠️ 未找到目标数据库配置 [database_target]")
            
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果提供了命令行参数，测试指定的数据库
        if sys.argv[1] == 'source':
            asyncio.run(test_connection('database_source', '源数据库'))
        elif sys.argv[1] == 'target':
            asyncio.run(test_connection('database_target', '目标数据库'))
        else:
            print("用法: python test_db.py [source|target]")
            print("不带参数则测试所有数据库")
    else:
        # 默认测试所有数据库
        asyncio.run(test_all_connections())
