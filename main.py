import sys
from pythom_bili import *

params = {
    'id': 436275,
    'str': '48265113',
    'test': 'abcdefg',
}
appkey = "1d8b6e7d45233436"
appsec = "560c52ccd288fed045859ed18bffd973"


print('操作选项：')
print('1:搜索视频')
print('2:下载视频')
choice = input('请选择您想要执行的操作：')
if choice == '1':
    search_keyword = str(input('请输入搜索内容：'))
    search_response = get_search(keyword=search_keyword)
    for i in range(0, len(search_response)-1):
        print(search_response[i]['bvid'] + '   ' + search_response[i]['title'])
elif choice == '2':
    pass
bvid = input('请输入视频bv号：')
print('获取视频信息中...')
video_info = get_info(bvid=bvid)
if video_info['code'] != 0:
    print('视频信息获取失败，错误码为' + str(video_info['code']))
    print('程序将在5秒后退出')
    time.sleep(5)
    sys.exit()

video_title = video_info['data']['title']
video_cid = video_info['data']['cid']
print('获取视频地址中...')
url = get_videourl(bvid=bvid, cid=video_cid)
if url['code'] != 0:
    print('视频地址获取失败，错误码为' + str(url['code']))
    print('程序将在5秒后退出')
    time.sleep(5)
    sys.exit()
for qn_number in range(len(url['data']['accept_description'])):
    print(str(url['data']['accept_quality'][qn_number]) + ':' + url['data']['accept_description'][qn_number])
qn = input('请输入你需要的分辨率：')
filepath = str(input('请输入视频保存路径，以”/“结尾'))
print('文件下载中...')
video = download(url=url['data']['durl'][0]['url'], name=video_title, output_path=filepath)
print('下载任务已结束，文件为' + video)
