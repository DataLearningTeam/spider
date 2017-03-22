# coding: utf-8

"""
直接执行本文本，会在当前目前目录创建文件夹spider_res来保存结果
"""

from bs4 import BeautifulSoup  # 用于解析网页中文, 安装： pip install beautifulsoup4
import os
import re
import time
import urllib2
import urlparse


def download(url, retry=2):
    """
    下载页面的函数，会下载完整的页面信息
    :param url:
    :param retry:
    :return:
    """
    print "downloading: ", url
    # 设置header信息，模拟浏览器请求
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'
    }
    try:
        request = urllib2.Request(url, headers=header)
        html = urllib2.urlopen(request, timeout=2).read()
    except urllib2.URLError as e:
        print "download error: ", e.reason
        html = None
        if retry > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                print e.code
                return download(url, retry - 1)
    time.sleep(1)
    return html


def getDOM(soap, domPath):
    '''
    筛选元素
    :param soap: soap化html页面
    :param domPath: 要筛选的元素dom路径
    :return:
    :return:
    '''
    res = soap
    for tag in domPath:
        for k in tag:
            res = res.find(k, tag[k])
    return res


def getRows(str):
    '''
    从soap之后text结果中获取行
    :param str:
    :return:
    '''
    res = []
    pattern = re.compile(r'( |\xa0)+')  # 替换空格
    str = pattern.subn(' ', str)
    pattern = re.compile(r"\n")
    rows = pattern.split(str[0])
    for row in rows:
        row = tripStr(row)
        if row != '':
            res.append(row)
    return res


def tripStr(str):
    '''
    去除行两端空格z
    :param str:
    :return:
    '''
    return str.strip()


def getHTags(soap, rows):
    '''
    获取所有h级别标签(h1->h6)
    :return:
    '''
    tags = [
        {'h1': '# '},
        {'h2': '## '},
        {'h3': '### '},
        {'h4': '#### '},
        {'h5': '##### '},
        {'h6': '###### '}
    ]

    repRows = []
    for tag in tags:  # 先找到tag，然后再修改rows
        for k in tag:
            items = soap.find_all(k)
            for item in items:
                txt = tripStr(item.text)
                if txt != '':
                    rep = "\n\n" + tag[k] + txt + "\n\n"
                    repRows.append({txt: rep})
    newRows = []
    for row in rows:
        row, repRows = replaceRow(row, repRows)
        newRows.append(row)

    return newRows


def replaceRow(row, repRows):
    '''
    替换行内容，匹配晚餐之后，从匹配堆中删除已经匹配的结果
    :param row: 要替换的行
    :param repRows: 要替换的内容列表
    :return:
    '''
    newRepRows = []
    for rep in repRows:
        for k in rep:
            if k != '':
                if row.find(k) != -1:
                    row = row.replace(k, rep[k])
                else:
                    newRepRows.append({k: rep[k]})  # 未被匹配的数据重新记入待匹配数据集中
            else:
                newRepRows.append({k: rep[k]})

    return row, newRepRows


def getPTags(soap):
    '''
    处理p标签
    :param soap:
    :return:
    '''
    repRows = []
    items = soap.find_all('p')
    for item in items:
        txt = tripStr(item.text)
        if txt != '':
            rep = tripStr(item.text) + "\n\n"
            repRows.append({txt: rep})
    return repRows


def getBoldTags(soap):
    '''
    获取所有粗体标签内容
    :param soap:
    :return:
    '''
    tags = [
        {'strong': '__%s__'},
        {'b': '__%s__'}
    ]
    repRows = []
    for tag in tags:
        for k in tag:
            items = soap.find_all(k)
            for item in items:
                txt = tripStr(item.text)
                if txt != '':
                    rep = tag[k] % (txt)
                    repRows.append({txt: rep})
    return repRows


def getATags(soap):
    '''
    获取a标签
    :param soap:
    :return:
    '''
    repRows = []
    items = soap.find_all('a')
    for item in items:
        txt = tripStr(item.text)
        if txt != '':
            url = item.get('href')
            rep = '%s[%s](%s)' % (txt, url, url)
            repRows.append({txt: rep})
    return repRows


def getCodeTags(soap):
    '''
    获取代码标签
    :param soap:
    :return:
    '''
    repRows = []
    items = soap.find_all('pre')
    for item in items:
        rows = getRows(item.text)
        newRows = []
        for txt in rows:
            if txt != '':
                newRows.append({txt: txt})

        if (newRows.__len__() > 0):
            for k in newRows[0]:
                newRows[0] = {k: "\n```\n%s" % newRows[0][k]}
            for k in newRows[-1]:
                newRows[-1] = {k: "%s\n```\n" % newRows[-1][k]}
            repRows = repRows + newRows
    return repRows


def getImgTags(soap, save=False):
    '''
    获取图片
    :param soap:
    :param save: 想保存图片到本地，true
    :return:
    '''
    repRows = []
    items = soap.find_all('div', {'class': 'image-package'})
    for item in items:
        imgUrl = item.find('img').get('src')
        imgUrl = imgUrl[: imgUrl.find('?')]

        if save == True:  # 下载图片到本地
            link = imgUrl
            path = link.split('/')
            name = path[-1]
            savePath = 'spider_res/' + name
            if os.path.exists(savePath) == False:
                source = download(link)
                if source != None:
                    file = open(savePath, 'wb')
                    file.write(source)
                    file.close()

        txt = tripStr(item.find('div', {'class': 'image-caption'}).text)  # 可能为空
        if txt == '':  # 无文本信息，url作为文本信息
            txt = imgUrl
        rep = "![%s](%s)\n%s" % (imgUrl, imgUrl, txt)
        repRows.append({txt: rep})
    return repRows


def getBQTags(soap):
    '''
    blockquote标签处理
    :param soap:
    :return:
    '''
    repRows = []
    items = soap.find_all('blockquote')
    for item in items:
        block = getRows(item.text)
        num = block.__len__()
        cur = 0
        for b in block:
            cur += 1
            b = tripStr(b)
            if b != '':
                rep = '> %s' % (b)
                if (cur == num):
                    rep = rep + "\n\n--\n"
                repRows.append({b: rep})
    return repRows


def getTitle(soap):
    '''
    获取文章标题
    :param soap:
    :return:
    '''
    # 文章标题 div.article->h1.title
    titlePath = [
        {'div': {'class': 'article'}},
        {'h1': {'class': 'title'}}
    ]
    # markdown一级标题
    title = tripStr(getDOM(soap, titlePath).string)
    return title


def getAuthor(soap):
    '''
    获取作者名字
    :param soap:
    :return:
    '''
    authorPath = [
        {'div': {'class': 'article'}},
        {'div': {'class': 'author'}},
        {'div': {'class': 'info'}}
    ]
    authorAll = getDOM(soap, authorPath)
    author = authorAll.find('span', {'class': 'tag'}).string + ': ' + authorAll.find('span', {'class': 'name'}).string
    return author


def crawlerOnePage(link):
    '''
    抓取单个网页
    :param link:
    :return:
    '''
    html = download(link)
    if html == None:
        return

    soap = BeautifulSoup(html, "html.parser")
    title = getTitle(soap)
    # file_name = 'spider_res/%s.md' % title
    # if os.path.exists(file_name):  # 文件存在，不处理
    #    return

    content = soap.find('div', {'class': 'show-content'})
    rows = getRows(content.text)
    pTags = getPTags(content)  # p标签需要最先处理
    newRows = []
    for row in rows:
        for p in pTags:
            for k in p:
                if k == '':
                    continue
                if row.find(k) != -1:
                    row = row.replace(k, p[k])
        newRows.append(row)

    rows = newRows
    rows = getHTags(content, rows)  # h标签需要单独处理
    reps = getBQTags(content)
    reps = reps + getCodeTags(content)
    reps = reps + getBoldTags(content)
    reps = reps + getATags(content)
    reps = reps + getImgTags(content)

    newRows = []
    for row in rows:
        row, reps = replaceRow(row, reps)
        newRows.append(row)

    if reps.__len__() > 0:  # 还有部分数据未被匹配，添加到最后
        for rep in reps:
            for k in rep:
                newRows.append(rep[k])

    author = getAuthor(soap)
    writeFile(title, author, link, newRows)


def writeFile(title, author, url, rows):
    if os.path.exists('spider_res/') == False:
        os.mkdir('spider_res')

    file_name = 'spider_res/' + title + '.md'
    if os.path.exists(file_name) == False:
        file = open(file_name, 'wb')
        title = '# ' + unicode(title).encode('utf-8', errors='ignore') + "\n\n"
        file.write(title)

        url = '[%s](%s)' % (url, url)
        url = unicode(url).encode('utf-8', errors='ignore') + "\n\n"
        file.write(url)

        author = unicode(author).encode('utf-8', errors='ignore') + "\n\n"
        file.write(author)
        for row in rows:
            row = unicode(tripStr(row)).encode('utf-8', errors='ignore') + "\n\n"
            file.write(row)
        file.close()


url_root = 'http://www.jianshu.com/'  # 网站根目录
url_seed = 'http://www.jianshu.com/c/9b4685b6357c?page=%d'  # 要爬取的页面地址模板
crawled_url = set()  # 已经爬取过的链接
flag = True

# step1 抓取文章链接
i = 1
while flag:
    url = url_seed % i
    i += 1

    html = download(url)
    if html == None:
        break

    soap = BeautifulSoup(html, "html.parser")
    links = soap.find_all('a', {'class': 'title'})
    if links.__len__() == 0:
        flag = False

    for link in links:
        link = link.get('href')
        if link not in crawled_url:
            realUrl = urlparse.urljoin(url_root, link)
            crawled_url.add(realUrl)  # 已爬取的页面记录下来，避免重复爬取
        else:
            print 'end'
            flag = False  # 结束抓取

paper_num = crawled_url.__len__()
print 'total paper num: ', paper_num

# step2 抓取文章内容,并按标题和内容保存起来
for link in crawled_url:
    crawlerOnePage(link)
