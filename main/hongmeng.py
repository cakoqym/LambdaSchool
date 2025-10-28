# coding=utf-8

"""
快乐玩耍
核心代码。
"""
import os
import time
import random
import json
from apscheduler.schedulers.blocking import BlockingScheduler
import itchat
from itchat.content import *
from main.common import (
    get_yaml
)
from main.utils import (
    get_bot_info,
    get_weather_info,
    get_dictum_info,
    get_diff_time,
)
from selenium import webdriver

reply_user_name_uuid_list = []
FILEHELPER_MARK = ['文件传输助手', 'filehelper']  # 文件传输助手标识
FILEHELPER = 'filehelper'

sweetie = ['厌物', '你脚下的蚂蚁', '专说骗人的诳话者', '黄天霸', 'cxk', '魔鬼的叔父', '哺乳类脊椎动物之一', '名字写在水上的人', 'BIG BAD WOLF', '你的兄弟']
sweet_words = sweetie[random.randint(0, 9)]



def autoReply(driver,text):
    time.sleep(10)
    elem = driver.find_element_by_css_selector('#prompt')
    elem.clear()
    elem.send_keys(text)

    driver.find_element_by_css_selector('#subm').click()
    time.sleep(90)

    completion = driver.find_element_by_css_selector('#result').text
    print(completion)
    time.sleep(50)
    assert "No results found." not in driver.page_source
    
    
def is_online(auto_login=False):
    """
    判断是否还在线。
    :param auto_login: bool,当为 Ture 则自动重连(默认为 False)。
    :return: bool,当返回为 True 时，在线；False 已断开连接。
    """

    def _online():
        """
        通过获取好友信息，判断用户是否还在线。
        :return: bool,当返回为 True 时，在线；False 已断开连接。
        """
        try:
            if itchat.search_friends():
                return True
        except IndexError:
            return False
        return True

    if _online(): return True  # 如果在线，则直接返回 True
    if not auto_login:  # 不自动登录，则直接返回 False
        print('微信已离线..')
        return False

    hotReload = not get_yaml().get('is_forced_switch', False)  # 切换微信号，重新扫码。
    loginCallback = init_wechat
    for _ in range(2):  # 尝试登录 2 次。
        if os.environ.get('MODE') == 'server':
            # 命令行显示登录二维码。
            itchat.auto_login(enableCmdQR=2, hotReload=hotReload, loginCallback=loginCallback)
            itchat.run(blockThread=False)
        else:
            itchat.auto_login(hotReload=hotReload, loginCallback=loginCallback)
            itchat.run(blockThread=False)
        if _online():
            print('登录成功')
            return True

    print('登录失败。')
    return False


@itchat.msg_register([TEXT])
def text_reply(driver,msg):
    """ 监听用户消息，用于自动回复 """
    try:
        # print(json.dumps(msg, ensure_ascii=False))

        uuid = msg.fromUserName  # 获取发送者的用户id
        # 如果用户id是自动回复列表的人员或者文件传输助手，则进行下一步的操作
        if uuid in reply_user_name_uuid_list or msg['ToUserName'] == FILEHELPER:
            receive_text = msg.text  # 好友发送来的消息内容
            # 通过图灵 api 获取要回复的内容。
            
            
            #reply_text = get_bot_info(receive_text, uuid)  # modifried
            reply_text = autoReply(driver,receive_text)

            time.sleep(5)  # 休眠一秒，保安全，想更快的，可以直接用。
            if reply_text:  # 如内容不为空，回复消息
                if msg['ToUserName'] == FILEHELPER:
                    reply_text = '机器人自动回复：{}'.format(reply_text)
                    itchat.send(reply_text, toUserName=FILEHELPER)
                    print('\n我发出信息：{}\n回复{}：'
                          .format(receive_text, reply_text))
                else:
                    msg.user.send(reply_text)
                    print('\n{}发来信息：{}\n回复{}：{}'
                          .format(msg.user.nickName, receive_text,
                                  msg.user.nickName, reply_text))
            else:
                if msg['ToUserName'] == FILEHELPER:
                    print('我发来信息：{} 自动回复失败'.format(receive_text))
                else:
                    print('{}发来信息：{} 自动回复失败'
                          .format(msg.user.nickName, receive_text))
    except Exception as e:
        print(str(e))


def init_wechat():
    """ 初始化微信所需数据 """
    conf = get_yaml()
    itchat.get_chatrooms(update=True)  # 更新群信息。

    for name in conf.get('auto_reply_names'):
        if name.lower() in FILEHELPER_MARK:  # 判断是否文件传输助手
            if FILEHELPER not in reply_user_name_uuid_list:
                reply_user_name_uuid_list.append(FILEHELPER)
        friends = itchat.search_friends(name=name)
        if not friends:  # 如果用户列表为空，表示用户昵称填写有误。
            print('自动回复中的昵称『{}』有误。'.format(name))
            continue
        else:
            name_uuid = friends[0].get('UserName')  # 取第一个用户的 uuid。
            if name_uuid not in reply_user_name_uuid_list:
                reply_user_name_uuid_list.append(name_uuid)


def send_alarm_msg():
    """ 发送定时提醒 """
    print('\n启动定时自动提醒...')
    conf = get_yaml()
    for gf in conf.get('girlfriend_infos'):
        weather = get_weather_info(gf.get('city_name'))
        dictum = get_dictum_info(gf.get('dictum_channel'))

        diff_time = get_diff_time(gf.get('start_date'))
        # sweet_words = gf.get('sweet_words')  # To Be Modified
        wechat_name = gf.get('wechat_name')
        if '宋清如' in dictum:
            dictum = '我是'+wechat_name+'至上主义者'
        send_msg = '\n'.join(x for x in [weather, dictum, sweet_words] if x)
        print(send_msg)

        if not send_msg or not is_online(): continue
        # 给微信好友发信息

        if wechat_name:
            if wechat_name.lower() in FILEHELPER_MARK:
                itchat.send(send_msg, toUserName=FILEHELPER)
                print('定时给『{}』发送的内容是:\n{}\n发送成功...\n\n'.format(wechat_name, send_msg))
            else:
                wechat_users = itchat.search_friends(name=wechat_name)
                if not wechat_users: continue
                wechat_users[0].send(send_msg)
                print('定时给『{}』发送的内容是:\n{}\n发送成功...\n\n'.format(wechat_name, send_msg))

        # 给群聊里发信息
        # group_name = gf.get('group_name')
        # if not group_name: continue
        # groups = itchat.search_chatrooms(name=group_name)
        # if not groups: continue
        # groups[0].send(send_msg)
        # print('定时给群聊『{}』发送的内容是:\n{}\n发送成功...\n\n'.format(group_name, send_msg))

    print('自动提醒消息发送完成...\n')


def init_alarm(driver):
    """ 初始化定时提醒 """
    alarm_info = get_yaml().get('alarm_info', None)
    if not alarm_info: return
    is_alarm = alarm_info.get('is_alarm', False)
    if not is_alarm: return
    alarm_timed = alarm_info.get('alarm_timed', None)
    if not alarm_timed: return
    hour, minute = [int(x) for x in alarm_timed.split(':')]

    # 检查数据的有效性
    for info in get_yaml().get('girlfriend_infos'):
        if not info: break  # 解决无数据时会出现的 bug。
        wechat_name = info.get('wechat_name', None)
        if (wechat_name and wechat_name.lower() not in FILEHELPER_MARK
                and not itchat.search_friends(name=wechat_name)):
            print('定时任务中的好友名称『{}』有误。'.format(wechat_name))

        # group_name = info.get('group_name')
        # if group_name and not itchat.search_chatrooms(name=group_name):
        # print('定时任务中的群聊名称『{}』有误。'
        # '(注意：必须要把需要的群聊保存到通讯录)'.format(group_name))

    # 定时任务
    scheduler = BlockingScheduler()
    # 每天9：30左右给女朋友发送每日一句
    scheduler.add_job(send_alarm_msg, 'cron', hour=hour,
                      minute=minute, misfire_grace_time=15 * 60)

    # # 每隔 30 秒发送一条数据用于测试。
    # scheduler.add_job(send_alarm_msg, 'interval', seconds=30)

    print('已开启定时发送提醒功能...')
    scheduler.start()


def run():
    """ 主运行入口 """
    conf = get_yaml()
    if not conf:  # 如果 conf，表示配置文件出错。
        print('程序中止...')
        return

    # 判断是否登录，如果没有登录则自动登录，返回 False 表示登录失败
    if not is_online(auto_login=True):
        return
    if conf.get('is_auto_relay'):
        print('已开启图灵自动回复...')

    driver = webdriver.Firefox()
    driver.get("https://www.thisstorydoesnotexist.com")
    
    init_alarm(driver) # 初始化定时任务
    





if __name__ == '__main__':
    run()
    #send_alarm_msg()
    pass
