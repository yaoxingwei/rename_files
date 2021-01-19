from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import requests
import time
import numpy
import cv2
import os
import json
import urllib.request
import sys
import re
import math
import xm_sign

def cbk(a, b, c):
    per = 100.0 * a * b / c
    if per > 100:
        per = 100
    print('%.2f%%' % per, end = '\r')

def get_chrome_drv():
    opt = Options()
    opt.add_argument('--no-sandbox')                # 解决DevToolsActivePort文件不存在的报错
    opt.add_argument('window-size=1920x3000')       # 设置浏览器分辨率
    opt.add_argument('--disable-gpu')               # 谷歌文档提到需要加上这个属性来规避bug
    opt.add_argument('--hide-scrollbars')           # 隐藏滚动条，应对一些特殊页面
    #opt.add_argument('blink-settings=imagesEnabled=false')      # 要验证码，不能打开。不加载图片，提升运行速度
    opt.add_argument('--headless')                  # 浏览器不提供可视化界面。Linux下如果系统不支持可视化不加这条会启动失败
    opt.add_experimental_option('w3c', False)       # get log must disable w3c
    caps = {
        'browserName': 'chrome',
        'loggingPrefs': {
            'browser': 'ALL',
            'driver': 'ALL',
            'performance': 'ALL',
        },
        'goog:chromeOptions': {
            'perfLoggingPrefs': {
                'enableNetwork': True,
            },
            'w3c': False,
        },
    }

    driver = webdriver.Chrome(options=opt, desired_capabilities=caps)
    driver.implicitly_wait(10)
    return driver

def parse_url_and_download(driver, host_url, folder, p_cnt):
    driver.get(host_url)
    time.sleep(2)
    xpath = '//*[@id="anchor_sound_list"]/div[2]/ul/li[' + '1' + ']/div[2]/a/span'
    ret = driver.find_element_by_xpath(xpath)
    ret.click()
    time.sleep(3)
    host_url = host_url.replace('p' + str(p_cnt) + '/', '')

    # play url
    play_url = driver.current_url
    first_trackid = play_url.replace(host_url, '')

    # get list url with first_trackid
    list_url = 'https://www.ximalaya.com/revision/play/v1/show?id=' + first_trackid + '&sort=0&size=30&ptype=1'

    xmly = xm_sign.ximalaya()
    res = xmly.getURLresp(list_url)

    for track in res['data']['tracksAudioPlay']:
        trackid = track['trackId']

        target_url = 'https://www.ximalaya.com/revision/play/v1/audio?id=' + str(trackid) + '&ptype=1'

        res = xmly.getInfos(target_url)
        #print(res['data']['src'])
        dl_url = res['data']['src']
        print("dl_url:%s" % dl_url)

        dl_path = '/srv/dev-disk-by-label-hot_drive/share/ximalaya/' + folder
        if os.path.exists(dl_path) == False:
            os.mkdir(dl_path)
            #os.system('mkdir ' + dl_path)
        dl_path = dl_path + '/'
        dl_file = str(track['index']).zfill(3) + '_' + track['trackName'] + '.m4a'

        urllib.request.urlretrieve(dl_url, dl_path + dl_file, cbk)
        print("download: %s to %s" % (dl_file, dl_path))

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Eg: ximalaya_dl.py <url> <download_folder_name>")

    url = sys.argv[1]
    folder = sys.argv[2]

    driver = get_chrome_drv()
    driver.get(url)
    time.sleep(2)
    res = driver.find_element_by_xpath('//*[@id="anchor_sound_list"]/div[1]/span[1]/span')
    #total_num = filter(str.isdigit, res.text)
    total_num = re.sub("\D", "", res.text)
    for p in range(1, math.ceil(int(total_num) / 30) + 1):
        new_url = url + 'p' + str(p) + '/'
        print(new_url)
        parse_url_and_download(driver, new_url, folder, p)
    driver.close()