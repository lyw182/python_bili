from functools import reduce
from hashlib import md5
import time
import hashlib
import urllib.parse
import urllib.request
import requests
import os

mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

def appsign(params, appkey, appsec):
    '为请求参数进行 APP 签名'
    params.update({'appkey': appkey})
    params = dict(sorted(params.items())) # 按照 key 重排参数
    query = urllib.parse.urlencode(params) # 序列化参数
    sign = hashlib.md5((query+appsec).encode()).hexdigest() # 计算 api 签名
    params.update({'sign':sign})
    return params

def getMixinKey(orig: str):
    '对 imgKey 和 subKey 进行字符顺序打乱编码'
    return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]

def signWbi(params: dict, img_key: str, sub_key: str):
    '为请求参数进行 wbi 签名'
    mixin_key = getMixinKey(img_key + sub_key)
    curr_time = round(time.time())
    params['wts'] = curr_time                                   # 添加 wts 字段
    params = dict(sorted(params.items()))                       # 按照 key 重排参数
    # 过滤 value 中的 "!'()*" 字符
    params = {
        k : ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
        for k, v 
        in params.items()
    }
    query = urllib.parse.urlencode(params)                      # 序列化参数
    wbi_sign = md5((query + mixin_key).encode()).hexdigest()    # 计算 w_rid
    params['w_rid'] = wbi_sign
    return params

def getWbiKeys() -> tuple[str, str]:
    '获取最新的 img_key 和 sub_key'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.bilibili.com/'
    }
    resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=headers,timeout=10)
    resp.raise_for_status()
    json_content = resp.json()
    img_url: str = json_content['data']['wbi_img']['img_url']
    sub_url: str = json_content['data']['wbi_img']['sub_url']
    img_key = img_url.rsplit('/', 1)[1].split('.')[0]
    sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
    return img_key, sub_key

def getInfo(bvid:str) -> dict:
    '获取视频信息'
    info_url = 'https://api.bilibili.com/x/web-interface/view'
    info_params = {'bvid':bvid}
    info = requests.get(url=info_url,params=info_params,timeout=10)
    if info.status_code == 0:
        return info.json()
    if info.status_code != 0:
        return {'code':info.status_code}

def getVideoUrl(bvid:str,cid:str,qn:str) -> str:
    '获取视频url'
    video_stream_url = 'https://api.bilibili.com/x/player/wbi/playurl'
    video_stream_params = {'bvid':bvid,'cid':cid,'qn':qn,'platform':'html5','high_quality':'1'}
    video_url = requests.get(url=video_stream_url,params=video_stream_params,timeout=10)
    if video_url.status_code == 0:
        return video_url.json()['data']['durl']['url']
    if video_url.status_code != 0:
        return video_url.status_code

def percent(a:int,b:int,c:int) -> int:
    '''获取下载进度百分比
    @a:已下载数据块
    @b:数据块大小
    @c:远程文件大小
    '''
    per = 100*a*b/c
    if per > 100:
        per = 100
    print(per)

def getVideo(url:str,name:str,dir:str=os.path.abspath('.')) -> str:
    '''下载视频'''
    filename = dir + name
    urllib.request.urlretrieve(url=url,filename=filename,reporthook=percent)
    return filename