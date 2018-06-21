# -*- coding: utf-8 -*-
import urlparse
# import re
import getopt
import md5
import os
from time import time
import time
import urlparse
import random
import urllib2
import HTMLParser
from bs4 import BeautifulSoup
import requests
import json
from queue import queue
from jsparse import MyParser
import sys
from processing import Process, Queue
import commands
import re
import json
import MySQLdb
import base64
import logging

reload(sys)
sys.setdefaultencoding('utf8')


class Spider(object):
	def __init__(self, pid, url, depth, maxlink, post, cookie, host, regex, authorization):
		self.result = queue()
		self.urlhashmap = {}
		self.thirdqueue = queue()
		tmp = {}
		tmp['host'] = host
		tmp['url'] = url
		tmp['post'] = post
		tmp['src'] = ''
		tmp['referer'] = url
		tmpqueue = queue()
		tmpqueue.push(tmp)
		self.urlhashmap[0] = tmpqueue  # 把第一个url(任务队列)放进第一层[0],从这网页中爬去的放在下一层[1],依次
		self.host = urlparse.urlparse(url)[1]
		# self.maxdepth 爬虫深度
		self.maxdepth = depth
		# self.maxlink 最多爬的url树木
		self.maxlink = maxlink
		# 正则匹配内容
		self.regex = regex
		self.auth = authorization
		self.post = post
		self.urlmd5 = []
		self.depth = 0
		self.pid = pid
		self.auth = authorization
		self.tmpqueue = queue()
		self.cookie = cookie
		self.headers = {"Content-Type": "application/x-www-form-urlencoded"}
		self.user_agent = "Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; HUAWEI MT1-T00 Build/HuaweiMT1-T00) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30 AlipayDefined(nt:WIFI,ws:480|805|1.5) AliApp(AP/8.6.0.040305) AlipayClient/8.6.0.040305"

	# 计算urlMD5用作去重
	def getMd5(self, url, post):
		try:
			urlpart = urlparse.urlparse(url)
			scheme = urlpart[0]
			netloc = urlpart[1]
			path = urlpart[2]
			params = urlpart[3]
			queryget = urlpart[4].split('&')
			queryget.sort()
			querypost = post.split('&')
			querypost.sort()
			frgment = urlpart[5]
			querygetkey = ""
			querypostkey = ""
			for var in queryget:
				querygetkey = querygetkey + var.split('=')[0]
			for var in querypost:
				querypostkey = querypostkey + var.split('=')[0]
			urlkey = netloc + path + params + \
			         frgment + querygetkey + querypostkey
			m = md5.new()
			m.update(urlkey)
			return m.hexdigest()
		except:
			return ""

	# url去重 域名不同 会给过滤掉
	def urlFilter(self, item, referer):
		if item['referer'] == "":
			item['referer'] = referer
		try:
			urlpart = urlparse.urlparse(str(item['url']))
		except Exception as e:
			return False

		urlmd5 = self.getMd5(item['url'], item['post'])

		if self.host == urlpart[1]:
			if urlmd5 not in self.urlmd5:
				self.urlmd5.append(urlmd5)
				self.result.push(item)
				depth = self.depth + 1
				if self.urlhashmap.has_key(depth):
					self.urlhashmap[depth].push(item)
				else:
					tmp = queue()
					tmp.push(item)
					self.urlhashmap[depth] = tmp
		else:
			if urlmd5 not in self.urlmd5:
				self.thirdqueue.push(item)
				self.urlmd5.append(urlmd5)

	def regularMacth(self, regpattern, inputstr):
		pattern = re.compile(regpattern, re.IGNORECASE)
		#	print pattern,inputstr
		try:
			m = pattern.findall(str(inputstr))
			if m:
				return m
			else:
				return False

		except Exception as e:
			return False

	def newProcExecuteCmd(self, queue, cmd):
		if cmd == "" or cmd == None:
			return False
		result = (commands.getstatusoutput(cmd))
		print result
		# print result
		if result[0] != 0:
			queue.put(-1)
			return
		queue.put(result[1])
		return

	def cmdrun(self, cmd):
		comScanCmd = cmd
		queue = Queue()
		scanProc = Process(
			target=self.newProcExecuteCmd, args=[queue, comScanCmd])
		scanProc.start()
		# 等待5秒
		scanProc.join(10)
		try:
			scanResult = queue.get(timeout=5)
		except Exception as e:
			print "get cmd result error"
			scanResult = -1
		scanProc.terminate()
		return scanResult

	def phantomjs_fetcher(self, pid, url, post):
		print(pid)
		url = url.replace('"', '\\"')
		self.post = post.replace('"', '\\"')
		self.cookie = self.cookie.replace('"', '\\"')
		# self.auth=self.auth.replace('"','\\"')
		if len(post) > 0:
			cmd = "/Users/taerg/Desktop/sp/phantomjs_taerg/phantomjs /Users/taerg/Desktop/sp/phantomjs_taerg/crawls.js  \"%s\" \"%s\" \"%s\" \"%s\" \"10\"" % (
				url, self.cookie, self.auth, post)
		else:
			cmd = "/Users/taerg/Desktop/sp/phantomjs_taerg/phantomjs /Users/taerg/Desktop/sp/phantomjs_taerg/crawls.js  \"%s\" \"%s\" \"%s\" \"\" \"10\"" % (
				url, self.cookie, self.auth)
		print cmd
		print cmd
		outputstr = self.cmdrun(cmd)
		if outputstr == -1:
			return
		# print outputstr

		url_part = self.regularMacth("hook_url:(.*)hook_url_end", outputstr)
		# print url_part
		print("***")
		print outputstr
		print("###")
		outputstr = outputstr.replace("\n", "")
		outputstr = outputstr.replace("\r", "")

		html_part = self.regularMacth(
			"crawl_content:(.*)content_end", outputstr)
		s = html_part[0]
		print(s)

		# hook 到的 urls
		for var in url_part:
			# print var
			var = json.loads(var)
			print "[+] hookurls:%s" % var['url']
			if var['method'] == "POST":
				r = {'url': var['url'], 'post': var[
					'post'], 'referer': '', 'tag': ''}
			else:
				r = {'url': var['url'], 'post': '', 'referer': '', 'tag': ''}
			self.urlFilter(r, url)

		# 分析渲染页面的 href
		soup = BeautifulSoup(s)
		p = MyParser(soup, url)
		p.parser()
		while p.tmpqueue.length() > 0:
			var = p.tmpqueue.pop()
			# print "[+]get href:%s" % var['url']
			self.urlFilter(var, url)

	def crawl(self):
		# 初始为self.depth ＝0
		while (self.depth <= self.maxdepth):
			if self.urlhashmap.has_key(self.depth) is False:  # 当前depth是否有网址\需要爬的东西
				print "-------------%s--------------" % self.depth
				break
			# 第二层时候 会发生多个请求
			while (self.urlhashmap[self.depth].length() > 0):  # 当前深度队列长度大于0
				# print self.depth
				urldata = self.urlhashmap[self.depth].pop()
				url = urldata['url']
				post = urldata['post']
				# print url,self.result.length()
				self.phantomjs_fetcher(pid, url, post)

				if self.result.length() >= int(self.maxlink):
					print "[-] Max link:", self.result.length()
					return
			i = self.urlhashmap[self.depth].length()
			self.depth = self.depth + 1
			print "-------------%s--------------" % self.depth


# def usage():
#     print "python spider.py -u url --cookie cookie -p post -d depth --maxlink maxlink --regex regex "

def add_html_to_pages(the_pid, the_url, the_html):
	try:
		conn = MySQLdb.connect(host='127.0.0.1', user='taerg', passwd='hivtaerg', port=3306)
		cur = conn.cursor()
		# cur.execute('create database if not exists taerg')
		conn.select_db('taerg')
		# cur.execute('create table test(id int,info varchar(20))')
		sqli = "insert into pages values(NULL,%s,%s,%s,now(),0,NULL,0)"
		# base64_html = the_html.encode('base64','strict')
		base64_html = base64.b64encode(the_html)
		cur.execute(sqli, (the_pid, the_url, base64_html))
		conn.commit()
		cur.close()
		conn.close()
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])


def the_main(pid, url, cookie):
	# cgi = "http://asocdb-2.alipay.net//#/myBank/test/event/manager"
	cgi = url
	post = ""
	cookie = cookie
	depth = "1"
	maxlink = "1000"
	regex = "悦悦"
	authorization = None
	logging.debug("[+] Crawl cgi:%s post:%s depth:%s maxlin:%s regex:%s",cgi,post,depth,maxlink,regex)
	host = urlparse.urlparse(cgi)[1]
	logging.debug('[+] Depth:%s', depth)
	logging.debug('[+] Maxlink:%s',maxlink)
	try:
		depth = int(depth)
	except:
		pass
	try:
		maxlink = int(maxlink)
	except:
		pass
	# print "[+] Auth:", authorization
	spider = Spider(
		pid, cgi, depth, maxlink, post, cookie, host, regex, authorization)
	spider.crawl()

	filename = "./result/" + host
	third_file_name = "./result/" + host + "_third"
	file_object = open(filename, 'w')
	third_file_obj = open(third_file_name, 'w')
	print "[+] Done crawl!"

	while spider.result.length() > 0:
		var = spider.result.pop()
		print "[+] Get url:", var['url'], ' post:', var['post'], spider.result.length()
		file_object.write("URL:")
		file_object.write(var['url'])
		file_object.write(" POST: ")
		file_object.write(var['post'])
		file_object.write(" TAG: ")
		file_object.write(var['tag'])
		file_object.write(" REFERER: ")
		file_object.write(var['referer'])
		file_object.write('\n')

	while spider.thirdqueue.length() > 0:
		var = spider.thirdqueue.pop()
		print "[+] Get thrid url:", var['url'], ' post:', var['post'], spider.result.length()
		third_file_obj.write("URL:")
		third_file_obj.write(var['url'])
		third_file_obj.write(" POST: ")
		third_file_obj.write(var['post'])
		third_file_obj.write(" TAG: ")
		third_file_obj.write(var['tag'])
		third_file_obj.write(" REFERER: ")
		third_file_obj.write(var['referer'])
		third_file_obj.write('\n')

	file_object.close()
	third_file_obj.close()


if __name__ == '__main__':
	logging.basicConfig(filename='taerg_spider.log', level=logging.DEBUG,  # 在这里调整输出到文件的等级
	                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
	                    datefmt='%a, %d %b %Y %H:%M:%S',
	                    filemode='w'
	                    )
	console = logging.StreamHandler()
	console.setLevel(logging.DEBUG)  # 在这里调整输出到屏幕的等级
	formatter = logging.Formatter('[line:%(lineno)d]%(levelname)s %(message)s')
	console.setFormatter(formatter)
	logging.getLogger('').addHandler(console)
	pid = 'pid'
	url = 'file:///Users/taerg/Desktop/xsstest/1.html'
	cookie = ''
	the_main(pid, url, cookie)
