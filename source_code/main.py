# -*- coding: utf-8 -*-

from flask import Flask, send_from_directory, send_file
from gevent import monkey
from gevent.pywsgi import WSGIServer
import os
import urllib
import sys
import html
import os
import webvtt
import asstosrt
import chardet
from tkinter import *
from tkinter import filedialog
import locale
import time

monkey.patch_all()
from flask_cors import *

app = Flask(__name__)
CORS(app, supports_credentials=True)

WORK_DIRECTORY = '/'
SEP = '/'
lang = locale.getdefaultlocale()[0]
IS_ZH = 'CN' in lang
BACK = "返回首页" if IS_ZH else 'back to index'
NAME = '仔仔文件传输助手' if IS_ZH else "ZZ file explorer"


@app.route('/')
def hello_world():
    return get_list_page(WORK_DIRECTORY)


@app.route("/static/<path:path>", methods=["GET"])
def static_dir(path):
    return send_from_directory('./static/', path)


@app.route("/file/<path:path>", methods=["GET"])
def get_file(path):
    print('getfile', path)
    suffix = path.split(".")
    suffix = suffix[-1] if suffix else ""
    path = urllib.parse.unquote(path)
    path = path.replace("@@", SEP)
    print(path)
    if path.endswith(SEP):  # 判断是否是文件夹
        return get_list_page(path)
    elif suffix not in ["exe", "bat"]:
        path = path.replace("@@", SEP)
        return send_file(path, conditional=True)


@app.route("/play/<path:path>", methods=["GET"])
def get_video_player(path):
    # show the user profile for that user
    print(path)
    r = []
    try:
        displaypath = urllib.parse.unquote(path,
                                           errors='surrogatepass')
    except UnicodeDecodeError:
        displaypath = urllib.parse.unquote(path)

    displaypath = html.escape(displaypath, quote=False)
    enc = sys.getfilesystemencoding()
    title = 'Player for %s' % displaypath
    r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
             '"http://www.w3.org/TR/html4/strict.dtd">')
    r.append('<html>\n<head>')

    r.append('<meta http-equiv="Content-Type" '
             'content="text/html; charset=%s">' % enc)
    r.append('<title>%s</title>\n</head>' % title)
    # r.append('<script src="/static/player.js"></script>'
    #          # '<script src="/static/videosub-0.9.9.js"></script>'
    #          )
    r.append('<body>\n<h1>%s</h1>' % title)
    r.append('<li><a href="%s">%s</a></li>'
             % ('/',
                html.escape(BACK, quote=False)))
    r.append(
        '\n<p align="center"><video id="mainPlayer"   controls="controls" width="640" height="480">')
    caption_path = getCaption(path.replace('@@', SEP)).replace(SEP, '@@')
    r.append('''
    <source src="/file/%s" type="video/mp4">
     <track id="video-caption" src="/file/%s"  
     kind="captions" srclang="zh" label="Chinese" default/>
    ''' % (path, caption_path))
    r.append('</video></p>\n\n')
    r.append('</body>\n</html>\n')
    return '\n'.join(r)


def get_list_page(path):
    """Helper to produce a directory listing (absent index.html).

    Return value is either a file object, or None (indicating an
    error).  In either case, the headers are sent, making the
    interface the same as for send_head().

    """

    try:
        list = os.listdir(path)
    except OSError as e:
        print(e)
        return None
    list.sort(key=lambda a: a.lower())
    r = []
    displaypath = html.escape(path, quote=False)
    enc = sys.getfilesystemencoding()
    title = NAME + ' Directory listing for %s' % displaypath
    r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
             '"http://www.w3.org/TR/html4/strict.dtd">')
    r.append('<html>\n<head>')
    r.append('<meta http-equiv="Content-Type" '
             'content="text/html; charset=%s">' % enc)
    r.append('<title>%s</title>\n</head>' % title)
    r.append('<body>\n<h1>%s</h1>' % title)
    r.append('<hr>\n<ul>')
    if path != WORK_DIRECTORY:  # 'a/b/c/'  -> 'a/b/'
        r.append('<li><a href="%s">%s</a></li>'
                 % ('/',
                    html.escape(BACK, quote=False)))

    for name in list:
        fullname = os.path.join(path, name)
        displayname = linkname = name
        # print(name, fullname)
        # Append / for directories
        if os.path.isdir(fullname):
            fullname = fullname + "/"
            displayname = name + "/"
            linkname = name + "/"

        suffix = linkname.split('.')[-1]
        if suffix in ['mp4', 'avi', 'mkv']:
            r.append('<li><a href="%s">%s</a></li>'
                     % ('/play/' + urllib.parse.quote(fullname.replace(SEP, "@@")),
                        html.escape(displayname, quote=False)))
        else:
            r.append('<li><a href="%s">%s</a></li>'
                     % ('/file/' + urllib.parse.quote(fullname.replace(SEP, "@@")),
                        html.escape(displayname, quote=False)))
    r.append('</ul>\n<hr>\n</body>\n</html>\n')
    return '\n'.join(r)


def getCaption(videoPath):
    # 根据video名称寻找字幕
    print('get caption',videoPath)
    vtt_exist, srt_exist, ass_exist,ssa_exist = False, False, False,False
    dir_path = os.path.dirname(videoPath)
    videoPath = videoPath.split('/')[-1]
    videoName = videoPath.split('.')[0]
    print(videoName)
    vtt_name = videoName + '.vtt'
    srt_name = videoName + '.srt'
    ass_name = videoName + '.ass'
    ssa_name = videoName + '.ssa'
    file_list = os.listdir(dir_path)
    for file_name in file_list:
        # print(file_name)
        if file_name == vtt_name:
            vtt_exist = True
        elif file_name == srt_name:
            srt_exist = True
        elif file_name == ass_name:
            ass_exist = True
        elif file_name == ssa_name:
            ssa_exist = True
    if vtt_exist:
        return os.path.join(dir_path, vtt_name)
    elif srt_exist:
        return srt2vtt(srt_name, dir_path)
    elif ass_exist:
        return ass2vtt(videoName, dir_path,ass_name)
    elif ssa_exist:
        return ass2vtt(videoName, dir_path,ssa_name)
    else:
        return ''


def srt2vtt(srt_name, dir_path):
    print('srt2vtt',srt_name)
    srt_path = os.path.join(dir_path, srt_name)
    with  open(file=srt_path, mode='rb')  as f3:  # 以二进制模式读取文件
        data = f3.read()  # 获取文件内容
        # print(data)
        f3.close()  # 关闭文件
        origin_charset = chardet.detect(data)['encoding']  # 检测文件内容
        print(origin_charset)

    convert_webvtt = webvtt.from_srt(srt_path)
    convert_webvtt.save()
    return convert_webvtt.file


def removeIfExists(file_path):
    if (os.path.exists(file_path)):
        os.remove(file_path)


def ass2vtt(video_name, dir_path,ass_name):
    # 编码转换 然后用pysub
    ass_path = os.path.join(dir_path, ass_name)
    print(ass_path)
    with  open(file=ass_path, mode='rb')  as f3:  # 以二进制模式读取文件
        data = f3.read()  # 获取文件内容
        # print(data)
        f3.close()  # 关闭文件
        origin_charset = chardet.detect(data)['encoding']  # 检测文件内容
        print(origin_charset)
    tmp_path = ass_path
    tmp_ass_path = os.path.join(dir_path, 'tmp.ass')
    if origin_charset != 'utf8':
        tmp_path = tmp_ass_path
        with open(tmp_path, 'wb') as tmp_file:
            data = data.decode(origin_charset).encode('utf8')
            tmp_file.write(data)
    with open(tmp_path,encoding='utf8') as f:
        srt_str = asstosrt.convert(f)
        print(srt_str)
    removeIfExists(tmp_ass_path)
    tmp_srt_path = os.path.join(dir_path, video_name + '.srt')
    with open(tmp_srt_path, 'w',newline="",encoding="utf8") as f:
        f.write(srt_str)
    return srt2vtt(tmp_srt_path, dir_path)


def get_ip():
    import socket
    ip = '本机ip'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    print(ip)
    return ip


def show_qcode(url):
    import qrcode
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=10, )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    img.show()


if __name__ == '__main__':
    # 或者app.debug = True #代码修改了就自动运行
    # app.run(host='0.0.0.0',port=30006,debug=True)
    try:
        if IS_ZH:
            print("请在弹出框里选择需要共享的目录")
        else:
            print('please select directory to share')
        window = Tk()
        window.withdraw()  # 主窗口隐藏
        WORK_DIRECTORY = filedialog.askdirectory(parent=window, initialdir="/",
                                                 title='choose the share directory')
        if not WORK_DIRECTORY:
            print('cancel')
            sys.exit(1)
        url = "http://%s:30007" % get_ip()
        print("共享目录 " if IS_ZH else 'share directory: ', WORK_DIRECTORY)
        print("服务器启动" if IS_ZH else 'server started  ')
        print(
            '用手机或电脑浏览器访问 %s (或扫描生成的二维码)即可访问共享目录内容' % url if IS_ZH else
            'open link %s with browser on PC/mobile (or just scan the QR code),to xisit your content' % url)
        show_qcode(url)
        WSGIServer(('0.0.0.0', 30007), app).serve_forever()
    except Exception as e:
        print(e)
        time.sleep(10)