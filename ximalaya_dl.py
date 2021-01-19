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

def config_chrome_and_get_target():
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

    #### login #####
    driver.get('https://www.ximalaya.com/')
    time.sleep(1)

    driver.find_element_by_xpath('//*[@id="rootHeader"]/div/div[2]/div/div/img').click()

    user = driver.find_element_by_xpath('//*[@id="accountName"]')
    passwd = driver.find_element_by_xpath('//*[@id="accountPWD"]')

    user.send_keys('')
    passwd.send_keys('')

    #找到登录按钮并点击
    driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/div/div/div[2]/div[3]/div[1]/div[2]/div/form/div[3]/button').click()

    #等待两秒，验证码加载完成
    time.sleep(1)

    #bg背景图片
    bg_img_src = driver.find_element_by_xpath('//*[@id="__xmca-container"]/div[1]/div[2]/img[1]').get_attribute('src')
    #front可拖动图片
    front_img_src = driver.find_element_by_xpath('//*[@id="__xmca-img-bl"]').get_attribute('src')

    #保存图片
    with open("bg.jpg", mode="wb") as f:
        f.write(requests.get(bg_img_src).content)

    with open("front.jpg", mode="wb") as f:
        f.write(requests.get(front_img_src).content)

    return driver

def cv_match_pic():
    bg = cv2.imread("bg.jpg")
    front = cv2.imread("front.jpg", 0)

    #将背景图片转化为灰度图片，将三原色降维
    bg = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    #将可滑动图片转化为灰度图片，将三原色降维
    #front = cv2.cvtColor(front, cv2.COLOR_BGR2GRAY)
    #front = front[front.any(1)]

    #用cv算法匹配精度最高的xy值
    result = cv2.matchTemplate(bg, front, cv2.TM_CCOEFF_NORMED)

    value = cv2.minMaxLoc(result)
    # 得到的value，如：(-0.1653602570295334, 0.6102921366691589, (144, 1), (141, 56))
    #print(value, "#" * 30)

    # 获取x坐标，如上面的144、141
    return value[2:][0][0], value[2:][1][0]

def enter_to_dl_url(driver, url, folder, p_cnt):
    for num in range(1, 31):
        driver.get(url)
        time.sleep(2)
        #driver.find_element_by_partial_link_text(str(num).zfill(2)).send_keys(Keys.ENTER)
        xpath = '//*[@id="anchor_sound_list"]/div[2]/ul/li[' + str(num) + ']/div[2]/a/span'
        ret = driver.find_element_by_xpath(xpath)
        if ret == 0:
            print("Can't find more items! Finished!")
            break
        else:
            ret.click()
        time.sleep(3)
        driver.find_element_by_xpath('//*[@id="award"]/main/div[1]/div[2]/div/div[2]/div/div[3]/div[1]/div/xm-player/div/i').click()
        time.sleep(3)

        requests = []
        for log in driver.get_log("performance"):
            x = json.loads(log['message'])['message']
            if x["method"] == "Network.requestWillBeSent":
                requests.append(
                    [
                        x["params"]["request"]["url"],
                        x["params"]["initiator"]["type"],
                        x["params"]["request"]["method"],
                        x["params"]["type"]
                    ]
                )
            else:
                pass

        search_str = 'https://www.ximalaya.com/revision/play/v1/audio' # TODO:
        target_url = ''

        for cnt in range(1, len(requests)):
            src_str = requests[cnt][0]
            if (src_str.find(search_str, 0, len(search_str)) != -1):
                #print(src_str)
                target_url = src_str
                break
        ### method 1 is invalid for xm_sign
        '''
        driver.get(target_url)

        page_str = driver.page_source
        page_str = page_str.partition('https')
        page_str = page_str[2].partition('m4a')

        dl_url = 'https' + page_str[0] + 'm4a'
        '''
        ### method 2 with xm_sign
        xima = xm_sign.ximalaya()
        res = xima.getInfos(target_url)
        #print(res['data']['src'])
        dl_url = res['data']['src']

        dl_path = '/srv/dev-disk-by-label-hot_drive/share/ximalaya/' + folder
        if num == 1:
            os.system('mkdir ' + dl_path)
        dl_path = dl_path + '/'
        num += (p_cnt - 1) * 30
        dl_file = str(num).zfill(3) + '.m4a'

        urllib.request.urlretrieve(dl_url, dl_path + dl_file, cbk)
        print("download: %s to %s" % dl_file, dl_path)
        #num += (p_cnt - 1) * 30

        #convert_file = str(num).zfill(3) + '.mp3'
        #print("gen %s to %s" % (convert_file, dl_path))
        #convert_cmd = 'ffmpeg -i ' + dl_path + dl_file + ' ' + dl_path + convert_file + ' >> ffmpeg.log'
        #os.system(convert_cmd)
    #rm_file = '/srv/dev-disk-by-label-hot_drive/share/ximalaya/' + folder + '/*.m4a'
    #rm_cmd = 'rm -f ' + rm_file
    #os.system(rm_cmd)

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

    driver = config_chrome_and_get_target()
    x,y = cv_match_pic()
    #print(x,y)

    div = driver.find_element_by_xpath('//*[@id="__xmca-block"]')
    #拖动滑块，以实际相反的y值代替x
    ActionChains(driver).drag_and_drop_by_offset(div, xoffset=(x - 35) // 0.946, yoffset=0).perform()

    #url = "https://www.ximalaya.com/ertong/45351682/"
    driver.get(url)
    time.sleep(2)
    res = driver.find_element_by_xpath('//*[@id="anchor_sound_list"]/div[1]/span[1]/span')
    #total_num = filter(str.isdigit, res.text)
    total_num = re.sub("\D", "", res.text)
    for p in range(1, math.ceil(int(total_num) / 30) + 1):
        new_url = url + 'p' + str(p) + '/'
        print(new_url)
        parse_url_and_download(driver, new_url, folder, p)
        #enter_to_dl_url(driver, new_url, folder, p)
    driver.close()

# TODO:
# 1. auto page turning -- done
# 2. get urls from config.ini
# 3. skip lock



