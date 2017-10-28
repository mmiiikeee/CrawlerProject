# -*- coding: utf-8 -*-
"""
Created on Sun May 15 00:16:13 2016

@author: Fuyuan Li
"""

# -*- coding:utf-8 -*-
from os.path import basename
import urllib.request
import urllib.error
import re
import os
# codecs用于写入unicode文本
import codecs


# 处理页面标签类
class Tool:
    # 去除img标签,7位长空格
    removeImg = re.compile('<img.*?>| {7}|')
    # 删除超链接标签
    removeAddr = re.compile('<a.*?>|</a>')
    # 把换行的标签换为\n
    replaceLine = re.compile('<tr>|<div>|</div>|</p>')
    # 将表格制表<td>替换为\t
    replaceTD = re.compile('<td>')
    # 把段落开头换为\n加空两格
    replacePara = re.compile('<p.*?>')
    # 将换行符或双换行符替换为\n
    replaceBR = re.compile('<br><br>|<br>')
    # 将其余标签剔除
    removeExtraTag = re.compile('<.*?>')

    def replace(self, x):
        x = re.sub(self.removeImg, "", x)
        x = re.sub(self.removeAddr, "", x)
        x = re.sub(self.replaceLine, "\n", x)
        x = re.sub(self.replaceTD, "\t", x)
        x = re.sub(self.replacePara, "\n    ", x)
        x = re.sub(self.replaceBR, "\n", x)
        x = re.sub(self.removeExtraTag, "", x)
        # strip()将前后多余内容删除
        return x.strip()


# 百度贴吧爬虫类
class BDTB:
    # 初始化方法，定义一些变量
    def __init__(self, baseUrl, seeLZ, floorTag):
        self.baseURL = baseUrl
        self.SeeLZ = '?see_lz=' + str(seeLZ)
        self.tool = Tool()
        self.file = None
        self.floor = 1
        self.defaultTitel = u"百度贴吧"
        self.floorTag = floorTag

    # 获取原始页面
    def getPage(self, pageIndex):
        try:
            if pageIndex == 0:
                url = self.baseURL + self.SeeLZ
            else:
                url = self.baseURL + self.SeeLZ + '&pn=' + str(pageIndex)
            print(url)
            # 构建请求的request
            # request = urllib.request.request(url)
            # 利用urlopen获取页面代码
            response = urllib.request.urlopen(url)
            # 将页面转化为特定编码 通过get_content_charset()
            # FIXME 可能的问题： 获取不到编码
            page = response.read().decode(
                response.headers.get_content_charset())
            return page

        # 连接失败错误
        except urllib.error.URLError as e:
            if hasattr(e, "reason"):
                print(u"连接百度贴吧失败,错误原因", e.reason)
                return None

        # 转化Unicode错误（应该不会出现，考虑删除）
        # 若出现错误，重新获取页面
        except UnicodeDecodeError:
            print('Unicode Error!!!')
            if pageIndex == 0:
                url = self.baseURL + self.SeeLZ
            else:
                url = self.baseURL + self.SeeLZ + '&pn=' + str(pageIndex)

            headers = {
                'User-Agent':
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) "
                "Gecko/20100101 Firefox/34.0"
            }
            # FIXME 可能有bug
            response = urllib.request.Request(url, headers)
            page = response.content
            return page

    # 获取页面标题
    def getTitle(self, page):
        title = re.findall('class="core_title_txt.*?>(.*?)</h', page)
        return title[0]

    # 获取页数
    def getPageNum(self, page):
        result = re.findall(
            '<li class="l_reply_num.*?</span>.*?<span.*?>(.*?)</span>', page)

        # 若出现多次页数，直接使用第一个出现的页数
        if (len(result) != 0):
            return result[0]
        else:
            return None

    # 获取页面内容
    def getContent(self, page):
        pattern = re.compile('<div id="post_content_.*?>(.*?)</div>', re.S)
        items = re.findall(pattern, page)
        contents = []
        for item in items:
            content = os.linesep + self.tool.replace(item) + os.linesep
            contents.append(content)
        return contents

    # 打开文本
    def setFileTitle(self, title):
        # 如果标题不是为None，即成功获取到标题
        if title is not None:
            self.file = codecs.open(title + ".txt", "w", encoding="utf-8")
        else:
            self.file = codecs.open(
                self.defaultTitel + ".txt", "w", encoding="utf-8")

    # 向文件写入每一楼的信息
    def writeData(self, contents):
        for item in contents:
            if self.floorTag == '1':
                # 楼与楼之间的分隔符
                floorLine = "\n" + str(
                    self.floor
                ) + u"------------------------------------------"
                "-----------------------------------------------" + os.linesep
                self.file.write(floorLine)
            self.file.write(item)
            self.floor += 1

    # 写入文本
    def start(self):
        indexPage = self.getPage(0)
        pageNum = self.getPageNum(indexPage)
        title = self.getTitle(indexPage)
        self.setFileTitle(title)
        print('标题:', title)
        contents = []
        if pageNum is None:
            print("URL已失效，请重试")
            return
        try:
            print("该帖子共有" + str(pageNum) + "页")
            for i in range(1, int(pageNum) + 1):
                print("正在写入第" + str(i) + "页数据")
                page = self.getPage(i)
                contents.extend(self.getContent(page))
            self.setFileTitle(title)
            self.writeData(contents)

        # 出现写入异常
        except IOError as e:
            self.file.close()
            print("写入异常，原因" + e)

        # 出现未知错误
        except Exception as e:
            print(u"异常：", e)

        # 关闭文件
        finally:
            self.file.close()
            print("写入任务完成")

    # 获取图片方法
    def getFig(self, page, title):
        img_urls = re.findall('class="BDE_Image".*?src="(.*?)"', page)
        for img_url in img_urls:
            try:
                # 获取图片数据
                img_data = urllib.request.urlopen(img_url).read()
                # 以网址最后的名称为文件名
                file_name = basename(urllib.parse.urlsplit(img_url)[2])
                # 打开图片文件，wb = write binary
                output = open(title + "\\" + file_name, 'wb')
                # 写入图片数据
                output.write(img_data)
                # 关闭图片文件
                output.close()
            except:
                # TODO 可能的错误处理
                pass

    # 获取图片
    def start2(self):
        indexPage = self.getPage(0)
        pageNum = self.getPageNum(indexPage)
        title = self.getTitle(indexPage)
        print('标题:', title)
        if pageNum is None:
            print("URL已失效，请重试")
            return
        try:
            print("该帖子共有" + str(pageNum) + "页")

            # 判断含有标题名字文件夹是否存在
            if not os.path.exists(title):
                # 创建文件夹
                os.mkdir(title)

            for i in range(1, int(pageNum) + 1):
                print("正在加载第" + str(i) + "页图片")
                page = self.getPage(i)
                self.getFig(page, title)

        # 出现写入异常
        except IOError as e:
            print("加载异常，原因" + e.message)
        finally:
            print("加载任务完成")


# 主函数
print(u"请输入帖子代号")
baseURL = 'https://tieba.baidu.com/p/' + str(
    input(u'https://tieba.baidu.com/p/'))

while True:
    seeLZ = input(u'是否只获取楼主发言，是输入1，否输入0\n')
    if seeLZ == '1' or seeLZ == '0':
        break
while True:
    floorTag = input(u'是否写入楼层信息，是输入1，否输入0\n')
    if floorTag == '1' or floorTag == '0':
        break

bdtb = BDTB(baseURL, seeLZ, floorTag)
while True:
    content = input(u'写入数据输入1，加载图片输入0\n')
    if content == '1':
        bdtb.start()
        break
    elif content == '0':
        bdtb.start2()
        break

# test example 5107094720
