import hashlib
import os
import time
import urllib.parse
import re
from functools import reduce
import httpx


mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]


#def appsign(params, appkey, appsec):
#    """为请求参数进行 APP 签名"""
#    params.update({'appkey': appkey})
#    params = dict(sorted(params.items()))  # 按照 key 重排参数
#    query = urllib.parse.urlencode(params)  # 序列化参数
#    sign = hashlib.md5((query + appsec).encode()).hexdigest()  # 计算 api 签名
#    params.update({'sign': sign})
#    return params

def get_cookies():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.bilibili.com/'
    }
    cookies = httpx.get(url='https://www.bilibili.com/', headers=headers)
    return cookies.cookies


def get_search(keyword: str):
    search_url = 'https://api.bilibili.com/x/web-interface/wbi/search/type'
    params = {'keyword': keyword, 'search_type': 'video'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.bilibili.com/'
    }
    search = httpx.get(url=search_url, headers=headers, cookies=get_cookies(), params=get_wbikeys(params=params))
    return search.json()['data']['result']


def get_mixinkey(orig: str):
    """对 imgKey 和 subKey 进行字符顺序打乱编码"""
    return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]


def get_wbikeys(params: dict) -> dict:
    """为请求参数进行 Wbi 签名
    @params:未签名参数
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.bilibili.com/'
    }
    wbikeys_url = 'https://api.bilibili.com/x/web-interface/nav'
    resp = httpx.get(url=wbikeys_url, headers=headers, timeout=10)
    resp.raise_for_status()
    json_content = resp.json()
    img_url: str = json_content['data']['wbi_img']['img_url']
    sub_url: str = json_content['data']['wbi_img']['sub_url']
    img_key = img_url.rsplit('/', 1)[1].split('.')[0]
    sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
    mixin_key = get_mixinkey(img_key + sub_key)
    curr_time = round(time.time())
    params['wts'] = curr_time  # 添加 wts 字段
    params = dict(sorted(params.items()))  # 按照 key 重排参数
    # 过滤 value 中的 "!'()*" 字符
    params = {
        k: ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
        for k, v
        in params.items()
    }
    query = urllib.parse.urlencode(params)  # 序列化参数
    wbi_sign = hashlib.md5((query + mixin_key).encode()).hexdigest()  # 计算 w_rid
    params['w_rid'] = wbi_sign
    return params


def get_info(bvid: str) -> dict:
    """获取视频信息
    @bvid:视频BV号
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.bilibili.com/'
    }
    info_url = 'https://api.bilibili.com/x/web-interface/view?'
    info_params = get_wbikeys({'bvid': bvid})
    info = httpx.get(url=info_url, headers=headers, params=info_params, timeout=10)
    if info.status_code == 200:
        return info.json()
    if info.status_code != 200:
        return {'code': info.status_code}


def get_videourl(bvid: str, cid: str) -> dict:
    """获取视频url
    @bvid:视频BV号
    @cid:视频cid，由get_info方法获取
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.bilibili.com/'
    }
    video_stream_url = 'https://api.bilibili.com/x/player/wbi/playurl?'
    video_stream_params = get_wbikeys({'bvid': bvid, 'cid': cid})
    video_url = httpx.get(url=video_stream_url, params=video_stream_params, headers=headers, timeout=10)
    return video_url.json()


def download(url: str, name: str, output_path: str = os.path.abspath('.')) -> str:
    """下载文件
    @url:下载url，一般由get_*提供
    @name:文件名，一般由get_*提供
    @output_path:保存位置
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.bilibili.com/'
    }
    filename = re.sub(pattern=r'/', repl=r' ', string=rf'{output_path}\{name}.mp4')
    with httpx.stream(method='GET', url=url, headers=headers) as response:
        with open(file=filename, mode='wb+') as w:
            for chunk in response.iter_raw():
                w.write(chunk)
    return filename
