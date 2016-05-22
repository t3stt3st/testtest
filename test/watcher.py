# -*- coding: utf-8 -*-
import requests
import argparse
import json
from lxml import html
import os
import MySQLdb
import logging
import hashlib
import re
# from tgitwatcher.models import  Tgitconfig,Tgitresult

class GitWatcher(object):
    def __init__(self,userid,config):
        self.userid = userid
        self.config = eval(config)
        self.number_page = None
        self.mark = ""
        self.name = ""
        self.link = ""
        self.contains = ""
        self.keywords = ""
        self.auditmark = 0
        logging.basicConfig(filename='mir_auto_trans.log', level=logging.DEBUG,  # 在这里调整输出到文件的等级
                            format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filemode='w'
                            )

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)  # 在这里调整输出到屏幕的等级
        formatter = logging.Formatter('[line:%(lineno)d]%(levelname)s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        parser = argparse.ArgumentParser(description='''
            o-O-o  o-o     o  o       o      o       o
              |   o     o  |  |       |      |       |
              |   |  -o   -o- o   o   o  oo -o-  o-o O--o o-o o-o
              |   o   | |  |   \ / \ /  | |  |  |    |  | |-' |
              o    o-o  |  o    o   o   o-o- o   o-o o  o o-o o
                    TGitWatcher
                    Github sensitive information scanner.
                    teams:IEG_SEC.
                    author: taergli''',
                                         formatter_class=argparse.RawDescriptionHelpFormatter, )
        parser.print_help()
        # self.tmodule = self.args.module



    def insert_to_db(self,mark,name,link,contains,keywords,auditmark):
        # Tgitresult.objects.create(user_id=self.userid,res_mark=mark,git_user=name,res_link=link,contains_lines=contains,key_words=keywords,audit_mark=auditmark)
        logging.debug(mark)
        logging.debug(name)
        logging.debug(link)
        logging.debug(contains)
        logging.debug(keywords)
        logging.debug(auditmark)


    def saveOutput(self,text):
        # if self.args.output is not None:
        #     arquivo = open(self.args.output, 'a')
        #     arquivo.write(text.encode("utf-8"))
        #     arquivo.close()
        pass

    def nextPage(self,prox_page):
        print("\n+[PAGE %s/%s]-----------------------------------------+" % (prox_page.split("&")[1].split("=")[1], self.number_page) )
        self.saveOutput("\n+[PAGE %s/%s]-----------------------------------------+\n" % (prox_page.split("&")[1].split("=")[1], self.number_page))
        HTML = self.accessWeb(prox_page)
        self.parseSearch(HTML.content)

    # def get_config(self):
    #     #
    #     # temp_config = {"query":"tencent",
    #     #                "filepath":"wp-admin.php",
    #     #                "keywords":["password","user"]
    #     #                }
    #     return temp_config

    def parseCode(self,url_arquivo,html_text):#传入html页面text
        if self.config is None:
            pass
        else:
            if "" != self.config["filepath"]:
                logging.debug(self.config["filepath"])
                logging.debug("url_arguivo:%s",url_arquivo)
                result = re.search(self.config["filepath"], url_arquivo)
                logging.debug("filepath find result:%s",result)
                if result == None:
                    return None
            for the_config in self.config["keywords"]:
                logging.debug(the_config)
                if re.search(the_config,html_text):
                    m = hashlib.md5()
                    m.update(self.name + self.link)
                    mark = m.hexdigest()
                    keywords = the_config
                    contains = the_config
                    self.insert_to_db(mark,self.name,self.link,contains,keywords,0)
                    # self.saveOutput("| [CONTAIN]: \"%s\" IN LINE: %s\n" % (self.config[self.args.module]['contains'], str(line)))#保存到文件


    def parseSearch(self,response):
        tree = html.fromstring(response)
        url_arquivo = tree.xpath('//div[contains(@class, "code-list-item-public")]/p[contains(@class, "title")]/a[2]/@href')#解析出所有找到的代码块的名称和链接行
        last_indexed = tree.xpath('//div[contains(@class, "code-list-item-public")]/p[contains(@class, "title")]\
                                  /span[contains(@class, "text-small text-muted updated-at")]/relative-time/text()')#解析出代码更新时间
        usuario = tree.xpath('//div[contains(@class, "code-list-item-public")]/a/img[contains(@class, "avatar")]/@alt')#解析出作者信息
        prox_page = tree.xpath('//a[contains(@class, "next_page")]/@href')#从页面中找出下一页链接
        for number_link in range(len(url_arquivo)):#每个页面有len(url_arquivo)个代码块
            link = self.url + url_arquivo[number_link].replace("blob","raw")#从页面显示的代码块,替换成代码所在的原始源文件
            HTML = self.accessWeb(link)
            html_text = HTML.text
            print("| [USER]: %s" % usuario[number_link])
            self.name = usuario[number_link]
            self.saveOutput("| [USER]: %s\n" % usuario[number_link])
            print("| [LINK]: %s" % link)
            self.link = link
            self.saveOutput("| [LINK]: %s\n" % link)
            print(len(last_indexed))
            print(last_indexed)
            print(number_link)
            print("| [ LAST INDEXED]: %s" % last_indexed[number_link])
            self.saveOutput("| [LAST INDEXED]: %s\n" % last_indexed[number_link])
            self.parseCode(url_arquivo[number_link],html_text)#url_arquivo是当前页面所有的文件路径,需要每次传一个
        if not prox_page:
            exit()
        prox_page = prox_page[0]
        prox_page = self.url + prox_page
        self.nextPage(prox_page)

    def accessWeb(self,url_acesso):
        acc = requests.get(url_acesso, headers=self.user_agent)
        if " find any code matching" in acc.text:
            print("[-] We couldn't find any code matching %s\n" % self.args.query)
            exit()
        return acc

    def parserPages(self,response):
        tree = html.fromstring(response)
        number_page = tree.xpath('//div[contains(@class, "pagination")]/a/text()')
        if number_page:
            return number_page[len(number_page)-2]
        else:
            return "1"

    def start(self):
        logging.debug("config:")
        logging.debug(self.config)
        logging.debug(type(self.config))
        self.url = "http://github.com"
        self.user_agent = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)\
                    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36"}
        self.search_term = "/search?o=desc&q=%s&s=indexed&type=Code&utf8=✓" % self.config['query']
        url_acesso = self.url + self.search_term
        HTML = self.accessWeb(url_acesso)
        self.number_page = self.parserPages(HTML.content)
        print("+[PAGE: 1/%s]-----------------------------------------+" % self.number_page)
        self.saveOutput("+[PAGE: 1/%s]-----------------------------------------+\n" % self.number_page)
        self.parseSearch(HTML.content)

a = GitWatcher("taerg",{"query":"tencnet", "filepath":"", "keywords":"passwords" })
a.start()