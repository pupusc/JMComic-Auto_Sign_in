import re
import requests
import json


def get_domains():
    """从发布页自动获取所有可用域名"""
    try:
        publish_url = 'https://jmcomicne.net/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(publish_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        domains = []

        # 匹配国际通用网域下的域名
        pattern_international = r'國際通用網域.*?(18comic\.[a-z]+)'
        match = re.search(pattern_international, response.text, re.DOTALL)
        if match:
            domains.append(match.group(1))

        # 匹配东南亚路线域名
        pattern_southeast = r'東南亞路線.*?(jmcomic-[a-z]+\.(one|org))'
        matches = re.findall(pattern_southeast, response.text, re.DOTALL)
        for match in matches:
            domains.append(match[0])

        # 匹配内地网域/分流域名
        pattern_mainland = r'https://(jm18c-[a-z]+\.(cc|me))'
        matches = re.findall(pattern_mainland, response.text)
        for match in matches:
            domains.append(match[0])

        # 去重并保持顺序
        seen = set()
        unique_domains = []
        for domain in domains:
            if domain not in seen:
                seen.add(domain)
                unique_domains.append(domain)

        if unique_domains:
            print(f"自动获取到 {len(unique_domains)} 个域名: {unique_domains}")
            return unique_domains
        else:
            # 如果匹配失败，使用默认域名列表
            print("未能自动获取域名，使用默认域名列表")
            return ['18comic.vip', '18comic.ink']
    except Exception as e:
        print(f"获取域名失败: {e}，使用默认域名列表")
        return ['18comic.vip', '18comic.ink']


def test_login(domain, payload, headers):
    """测试域名是否可以成功登录"""
    try:
        login_url = f'https://{domain}/login'
        with requests.Session() as session:
            response = session.post(login_url, data=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                response_data = json.loads(response.text)
                if response_data.get("status") == 1:
                    return True, session
                else:
                    print(f"域名 {domain} 登录失败: {response_data.get('errors')}")
                    return False, None
            else:
                print(f"域名 {domain} 请求失败，状态码: {response.status_code}")
                return False, None
    except Exception as e:
        print(f"域名 {domain} 连接失败: {e}")
        return False, None

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

# 用户名和密码 - 优先从环境变量读取，支持 GitHub Actions
payload = {
    # 'username': os.getenv('JM_USERNAME', 'username'),
    # 'password': os.getenv('JM_PASSWORD', 'password'),
    'username': 'pupusc',
    'password': '..52t1314..',
    'submit_login': '1',
}

# 获取所有可用域名
DOMAINS = get_domains()


# 轮询尝试每个域名直到登录成功
session = None
success_domain = None

print(f"\n开始轮询尝试 {len(DOMAINS)} 个域名...\n")
for domain in DOMAINS:
    print(f"正在尝试域名: {domain}")
    success, session = test_login(domain, payload, headers)

    if success:
        success_domain = domain
        print(f"✓ 域名 {domain} 登录成功！\n")
        break
    else:
        print(f"✗ 域名 {domain} 不可用，尝试下一个...\n")

if not success_domain:
    print("所有域名都无法登录，请检查账号密码或稍后重试")
    exit(1)

# 使用成功登录的域名构建URL
LOGIN_URL = f'https://{success_domain}/login'
SIGN_URL = f'https://{success_domain}/ajax/user_daily_sign'
LOGOUT_URL = f'https://{success_domain}/logout'

# 发送登录请求
with requests.Session() as session:
    LOGIN_response = session.post(LOGIN_URL, data=payload, headers=headers)
    
    # 成功返回200，不成功返回301
    if LOGIN_response.status_code == 200:

        #获取返回的json判断是否登录成功
        response_data = json.loads(LOGIN_response.text)

        #成功 {"status":1,"errors":["https:\/\/18comic-hok.xyz"]}
        #失败 {"status":2,"errors":["\u65e0\u6548\u7684\u7528\u6237\u540d\u548c\/\u6216\u5bc6\u7801!"]}
        if response_data["status"] == 1:
            print("账号登录成功\n")

            # 输出登录成功后的cookie
            cookies = session.cookies.get_dict()
            print("Cookies:")
            for key, value in cookies.items():
                print(f"{key}: {value}")
            print("")

            # 访问签到
            SIGN_response = session.post(SIGN_URL, headers=headers)

            # 返回签到内容
            SIGN_response_data = json.loads(SIGN_response.text)
            if "error" in SIGN_response_data:
                print("签到失败,你已经签到过了")
            else:  
                print("签到成功:", SIGN_response_data['msg'])
                print("自动签到执行完成！")                
            print()
            #返回 {"msg":""} 没有登录
            #返回 {"msg":"","error":"finished"} 已经签到过了
            #返回 {"msg":"\u60a8\u5df2\u7d93\u5b8c\u6210\u6bcf\u65e5\u7c3d\u5230\uff0c\u7372\u5f97 [ JCoin:20 ]  [ EXP:20 ] \n"} 签到成功

            # 退出账号
            LOGOUT_response = session.get(LOGOUT_URL, headers=headers)

            # 退出账号会发生重定向，查找重定向网页内容来判断是否退出成功,内容很多很卡
            # if "您现在已经登出!" in LOGOUT_response.text:
            #     print("账号登出成功!")
            # else:
            #     print("账号退出失败!")


            # 输出cookie判断是否退出
            # cookies = session.cookies.get_dict()
            # print("Cookies:")
            # for key, value in cookies.items():
            #     print(f"{key}: {value}")
            

            # 访问签到页面判断是否登出，返回 {"msg":""} 就是退出了
            SIGN_response = session.post(SIGN_URL, headers=headers)
            if not "error" in json.loads(SIGN_response.text):
                print("账号登出成功")
            else:
                print("账号登出失败")
        else:
            print("登录失败:", response_data['errors'])
    else:
        print("登录失败")
