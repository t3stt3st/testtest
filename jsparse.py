# -*- coding: utf-8 -*-
import urlparse
from queue import queue
import logging


class MyParser():
	def __init__(self, soup, url):
		self.tmpqueue = queue()
		self.url = url
		self.post = ""
		self.method = ""
		self.tmp = ""
		self.soup = soup

	# print "AAAA:",self.url

	def handle_iframe(self):
		# print "[+] Handle iframe"
		for link in self.soup.find_all("iframe"):
			tmp = {}
			try:
				link, host = self.handle_url(link.get('src'))
				tmp['url'] = link
				tmp['post'] = ""
				tmp['tag'] = "iframe"
				tmp['host'] = host
				tmp['referer'] = self.url
				self.tmpqueue.push(tmp)
			except Exception as e:
				print "[+] Exception:",str(e)
				pass
			logging.debug("[+] Get iframe src:%s",link)

	def handle_tag(self, tag, src):
		# print "[+] Handle tag"
		for link in self.soup.find_all(tag):
			# print "[+] Link:",link
			try:
				link, host = self.handle_url(link.get(src))
				# print "[+] Get link:",link
				tmp = {}
				tmp['url'] = link
				tmp['post'] = ""
				tmp['tag'] = tag
				tmp['host'] = host
				tmp['referer'] = self.url
				self.tmpqueue.push(tmp)
			except Exception as e:
				# print "[+] Exception:",str(e)
				pass

	def parser(self):
		formlist = self.soup.find_all('form')
		for html in formlist:
			self.handle_form(html, self.url)
		self.handle_tag('a', 'href')
		self.handle_tag('link', 'href')
		self.handle_tag('area', 'href')
		self.handle_tag('img', 'src')
		self.handle_tag('embed', 'src')
		self.handle_tag('video', 'src')
		self.handle_tag('audio', 'src')
		self.handle_iframe()

	def handle_form(self, form, url):
		# print "[+] Handle form"
		try:
			action = form['action']
			method = form['method']
		except Exception as e:
			#    print "[-] Exception:",str(e)
			return False
		logging.debug("form:%s",form)
		urlpart = urlparse.urlparse(url)
		tmp = {}
		tmp['tag'] = "form"
		tmp['host'] = ""
		tmp['referer'] = self.url
		tmp['post'] = ""
		poststr = ""
		url = ""
		if action == "":
			url = urlpart[0] + "://" + urlpart[1] + urlpart[2]
		else:
			url, host = self.handle_url(action)
		logging.debug("Get url:%s",url)
		# print "[+] Get url:",url
		#    print "[+] Action: ",action," Method:",method
		inputlist = form.find_all('input')
		logging.debug("inputlist:%s",inputlist)
		#    print "[+] ",inputlist
		for var in inputlist:
			try:
				tagtype = var['type']
			except Exception as e:
				tagtype = ""
				print "[-] No type value!"
			if tagtype != 'submit':
				try:
					name = var['name']
					value = ""
					if tagtype == "hidden":
						value = var['value']
					if poststr == "":
						poststr = name + "=" + value
					else:
						poststr = poststr + "&" + name + "=" + value
				except Exception as e:
					print "[-] No name!"
					pass
		selectlist = form.find_all('select')
		for var in selectlist:
			try:
				name = var['name']
				if poststr == "":
					poststr = name + "="
				else:
					poststr = poststr + "&" + name + "="
			except Exception as e:
				print "[-] No name!"
				pass
		textarea = form.find_all('textarea')
		for var in textarea:
			try:
				name = var['name']
			except Exception as e:
				print "[-] Exception:", str(e)
				name = ""
			if poststr != "":
				poststr = name + "="
			else:
				poststr = poststr + "&" + name + "="
		if method.lower() == "post":
			tmp['post'] = poststr
		else:
			url = url + "&" + poststr
		url, host = self.handle_url(url)
		tmp['url'] = url
		tmp['host'] = host
		self.tmpqueue.push(tmp)

	def getqueue(self):
		return self.tmpqueue

	def getAbsPath(self, urlpath, href):
		#    print "[+] Original:",urlpath, href
		index = 1
		key = False
		abspath = ""
		if urlpath == "":
			return '/' + href
		while key is False:
			if urlpath[len(urlpath) - index:len(urlpath) - index + 1] == "/":
				key = True
				abspath = urlpath[0:len(urlpath) - index + 1]
			else:
				key = False
				index = index + 1
		# 过滤掉./,并将相对路径转换为绝对路径
		if href.find("./") == 0:
			href = href[2:]
		hrefpart = href.split("../")
		pathpart = abspath.split("/")
		splitkey = len(hrefpart) - 1
		key = splitkey
		while key > 0:
			del pathpart[len(pathpart) - 2]
			key = key - 1
		while splitkey > 0:
			del hrefpart[0]
			splitkey = splitkey - 1
		return '/'.join(pathpart) + hrefpart[0]

	def handle_url(self, link):
		try:
			base = self.soup.find("base")
			try:
				base_url = base.get("href")
			except Exception as e:
				pass
			# print "[-] Error:",str(e)
			#        print "[+] Base_url:",base_url," Type:",type(base_url)
			if base_url is None or base_url == "":
				self.url = self.url
			else:
				self.url = base_url
		except Exception as e:
			pass
		# print "[-] No base element!"
		if link is None:
			return False
		urllist = urlparse.urlparse(self.url)
		urlpath = urllist[2]
		# print "[+] Get Link:",link
		if link.find('http') < 0:
			if link.find('//') == 0:
				link = "http:" + link
				return link, urlparse.urlparse(link)[1]
			if link.find("/") == 0:
				link = urllist[0] + "://" + urllist[1] + link
				return link, urllist[1]
			else:
				link = urllist[0] + "://" + urllist[1] + self.getAbsPath(urlpath, link)
				return link, urllist[1]
		else:
			return link, urlparse.urlparse(link)[1]
