# -*- coding: utf-8 -*-
"""
Created on Sun May 15 00:16:13 2016

@author: Fuyuan Li
"""

# -*- coding:utf-8 -*-
from urlparse import urlsplit
from os.path import basename
import urllib
import urllib2
import re
import thread
import time
import os
import sys
import requests
import json
import codecs

#处理页面标签类
class Tool:
    #去除img标签,7位长空格
    removeImg = re.compile('<img.*?>| {7}|')
    #删除超链接标签
    removeAddr = re.compile('<a.*?>|</a>')
    #把换行的标签换为\n
    replaceLine = re.compile('<tr>|<div>|</div>|</p>')
    #将表格制表<td>替换为\t
    replaceTD= re.compile('<td>')
    #把段落开头换为\n加空两格
    replacePara = re.compile('<p.*?>')
    #将换行符或双换行符替换为\n
    replaceBR = re.compile('<br><br>|<br>')
    #将其余标签剔除
    removeExtraTag = re.compile('<.*?>')
    def replace(self,x):
        x = re.sub(self.removeImg,"",x)
        x = re.sub(self.removeAddr,"",x)
        x = re.sub(self.replaceLine,"\n",x)
        x = re.sub(self.replaceTD,"\t",x)
        x = re.sub(self.replacePara,"\n    ",x)
        x = re.sub(self.replaceBR,"\n",x)
        x = re.sub(self.removeExtraTag,"",x)
        #strip()将前后多余内容删除
        return x.strip()

#百度贴吧爬虫类
class BDTB:

    #初始化方法，定义一些变量
    def __init__(self,baseUrl,seeLZ,floorTag):
        self.baseURL = baseUrl
        self.SeeLZ = '?see_lz='+str(seeLZ)
        self.tool = Tool()
        self.file = None
        self.floor = 1
        self.defaultTitel = u"百度贴吧"
        self.floorTag = floorTag
       
    def getPage(self,pageIndex):
        try:
            if pageIndex == 0:
                url = self.baseURL + self.SeeLZ
            else:
                url = self.baseURL + self.SeeLZ + '&pn=' + str(pageIndex)
            print(url)
            #构建请求的request
            request = urllib2.Request(url)
            #利用urlopen获取页面代码
            response = urllib2.urlopen(request)
            #将页面转化为UTF-8编码
            page = response.read()
#            raise Exception("Stop!")
#            page.encode('utf-8').strip()
            
            
#            headers = {
#            'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0"}
#            response = requests.post(url, headers)
#            print(response)
#            answer_list = response.json()["msg"]
#            page = ''.join(answer_list)
#            page = response.content
#            img_urls = re.findall('img .*?src="(.*?_b.*?)"', ''.join(answer_list))
#            try:
#                page = response.read().decode('utf-8')
            return page
#            except UnicodeDecodeError:
#                print('UnicodeDecodeError')
#                return 
            #return response.read().decode('utf-8')
            #response.read().decode('utf-8')

        except urllib2.URLError, e:
            if hasattr(e,"reason"):
                print u"连接百度贴吧失败,错误原因",e.reason
                return None
        except UnicodeDecodeError:
            print('Unicode Error!!!')
            if pageIndex == 0:
                url = self.baseURL + self.SeeLZ
            else:
                url = self.baseURL + self.SeeLZ + '&pn=' + str(pageIndex)
                
            headers = {'User-Agent': 
                        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0"}
            response = requests.post(url, headers)
            page = response.content
            return page

    def getTitle( self,page):
        #page = self.getPage(1)
 #       pattern = re.compile('<h3 class="core_title_txt.*?>(.*?)</h3>',re.S)
 #       result = re.search(pattern,page)
        title = re.findall('class="core_title_txt.*?>(.*?)</h', page)
        return title[0].decode('utf-8')
#        map(unicode,''.join(title))
#        """
#        unicode 还是没解决
#        """
#        
##        title = ''.join(title)
#        print(type(title))
#        print(title,len(title))
#        if(len(title) == 0):
#            return 'tieba'
#        else:
#            return title
        """
        if result:
            return result.group(1).strip()
        else:
            return self.defaultTitel
        """
            
    def getPageNum(self,page):
        #page = self.getPage(1)
#        pattern = re.compile('<li class="l_reply_num.*?</span>.*?<span.*?>(.*?)</span>',re.S)
        result = re.findall('<li class="l_reply_num.*?</span>.*?<span.*?>(.*?)</span>', page)
#        print 'result is: ', result
        
        if(len(result) != 0): # result:
            return result[0]
        else:
            return None
            
    def getContent(self,page):
        pattern = re.compile('<div id="post_content_.*?>(.*?)</div>',re.S)
        items = re.findall(pattern,page)
        contents = []
        for item in items:
            content = os.linesep + self.tool.replace(item)+ os.linesep
            contents.append(content.decode('utf-8'))
        return contents
        
    def setFileTitle(self,title):
        #如果标题不是为None，即成功获取到标题
        if title is not None:
            self.file = codecs.open(title + ".txt","wU", encoding = "utf-8")
        else:
            self.file = codecs.open(self.defaultTitel + ".txt","wU", encoding = "utf-8")

#    def writeData(self,contents):
#        #向文件写入每一楼的信息
#        for item in contents:
#            if self.floorTag == '1':
#                #楼之间的分隔符
#                floorLine = "\n" + str(self.floor) + u"-----------------------------------------------------------------------------------------\n"
#                self.file.write(floorLine)
#            self.file.write(item)
#            self.floor += 1
 
    def start(self):
        indexPage = self.getPage(0)
        pageNum = self.getPageNum(indexPage)
        title = self.getTitle(indexPage)
#        self.setFileTitle(title)
        print title
        contents = []
        if pageNum == None:
            print "URL已失效，请重试"
            return
        try:
            print "该帖子共有" + str(pageNum) + "页"
            for i in range(1,int(pageNum)+1):
                print "正在写入第" + str(i) + "页数据"

                page = self.getPage(i)
                contents.extend(self.getContent(page))
            print contents
            self.setFileTitle(title)
            for c in contents:
                if self.floorTag == '1':
#                #楼之间的分隔符
                    floorLine = "\n" + str(self.floor) + u"-----------------------------------------------------------------------------------------" + os.linesep
                    self.file.write(floorLine)
                self.file.write(c)
                self.floor += 1
                
        #出现写入异常
        except IOError,e:
            self.file.close()
            print "写入异常，原因" + e.message
            
        except Exception as e:
            print u"异常：" , e.message
            
        finally:
            self.file.close()
            print "写入任务完成"
            
    def getFig(self,page,title):
#        img_urls = re.findall('img .*?src="(.*?.*?)"', content)
        img_urls = re.findall('class="BDE_Image".*?src="(.*?)"', page)
        for img_url in img_urls:
            try:
                img_data = urllib2.urlopen(img_url).read()
                file_name = basename(urlsplit(img_url)[2])
                output = open(title + "\\" + file_name, 'wb')
                output.write(img_data)
                output.close()
            except:
                pass
        
    def start2(self):
        indexPage = self.getPage(0)
        pageNum = self.getPageNum(indexPage)
        title = self.getTitle(indexPage)
        if pageNum == None:
            print "URL已失效，请重试"
            return
        try:
            print "该帖子共有" + str(pageNum) + "页"
            
            if not os.path.exists(title):
                os.mkdir(unicode(title))

            for i in range(1,int(pageNum)+1):
                print "正在加载第" + str(i) + "页图片"
                page = self.getPage(i)
#                page = re.findall('"left_section" (.*?) "right_section', page)
                self.getFig(page,title)

        #出现写入异常
        except IOError,e:
            print "加载异常，原因" + e.message
        finally:
            print "加载任务完成"
            
print u"请输入帖子代号"
baseURL = 'https://tieba.baidu.com/p/' + str(raw_input(u'https://tieba.baidu.com/p/'))
while True:
    seeLZ = raw_input(u'是否只获取楼主发言，是输入1，否输入0\n')
    if seeLZ == '1' or seeLZ == '0':
        break
while True:
    floorTag = raw_input(u'是否写入楼层信息，是输入1，否输入0\n')
    if floorTag == '1' or floorTag == '0':
        break
    
bdtb = BDTB(baseURL,seeLZ,floorTag)

while True:
    content = raw_input(u'写入数据输入1，加载图片输入0\n')
    if content == '1':
        bdtb.start()
        break
    elif content == '0':
        bdtb.start2()
        break

#test example 5107094720
