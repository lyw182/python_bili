from sys import exit
from time import sleep
import alldef

print('操作选项：\n1:下载视频')
choice = input('请选择您想要执行的操作：')
bvid = input('请输入视频bv号：')
qn = input('请输入你需要的分辨率：\n16:360P 流畅\n32:480P 清晰\n64:720P 高清')
if choice == '1':
    print('获取视频信息中...')
    video_info = alldef.getInfo(bvid=bvid)
    print(video_info)
    if video_info['code'] != 0:
        print('视频信息获取失败，错误码为' + str(video_info['code']))
        print('程序将在5秒后退出')
        sleep(5)
        exit() 
    
    video_title = video_info['data']['title']
    video_cid = video_info['data']['cid']
    print('获取视频地址中...')
    url = alldef.getVideoUrl(bvid=bvid,cid=video_cid,qn=qn)
    print('文件下载中...')
    filename = alldef.getVideo(url=url,name=video_title)
    print('下载任务已结束')

