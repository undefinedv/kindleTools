#encoding:utf8
import sys
import smtplib
import re
import requests
import urllib
import json
import codecs
import subprocess
from threading import Thread
from email import encoders
from email.header import Header
from email.utils import parseaddr, formataddr
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart

from config import ktconfig
reload(sys)
sys.setdefaultencoding("utf8")

def send_email(attach, filename, ktconfig):

	msg = MIMEMultipart()
	msg["subject"] = "Convert"
	msg["from"]    = ktconfig['from_addr']
	msg["to"]      = ktconfig['kindle_email']
	htmlText = "kindle reader delivery."
	msg.preamble = htmlText
	msgText = MIMEText(htmlText, 'html', 'utf-8')  
	msg.attach(msgText)

	print filename
	with open(attach, 'rb') as f:
		att = MIMEText(f.read(), 'base64', 'utf-8')
		att["Content-Type"] = 'application/octet-stream'
		att["Content-Disposition"] = 'attachment; filename="%s.txt"' % (filename)
		msg.attach(att)

		# 设置附件的MIME和文件名，这里是txt类型:
	if ktconfig['mail_ssl'] == True:
		server = smtplib.SMTP_SSL(timeout = 60)
	else:
		server = smtplib.SMTP_SSL(timeout = 60)
	server.connect(ktconfig['smtp_server'], ktconfig['smtp_port'])
	server.ehlo()
	server.set_debuglevel(1)

	server.login(ktconfig['from_addr'], ktconfig['password'])
	server.sendmail(ktconfig['from_addr'], ktconfig['kindle_email'], msg.as_string())
	server.close()


def get_bookId(keywords):

	url = "http://zhannei.baidu.com"+"/cse/search?q="+urllib.quote(keywords)+"&p=0&s=5541116575338011306"
	req = requests.get(url = url)
	data = req.content
	p1 = "<a cpos=\"title\" href=\"(.*)\" title=\"(.*)\" class=\"result-game-item-title-link\" target=\"_blank\">"
	books = re.findall(p1, data)
	book_len = len(books)
	for i in xrange(0, book_len):
		print i,":",books[i][1],books[i][0]
	choose = raw_input("\033[1;32;40mPlease tell me which book you want:\033[0m")
	choose = int(choose)
	if choose >= book_len:
		printRed("invalid choice")
		exit()
	return books[choose]

def printGreen(data):
	print "\033[1;32;40m"+ str(data) + "\033[0m"

def printRed(data):
	print "\033[1;31;40m"+ str(data) + "\033[0m"

def sub_chapter(url, cid):
	global chapter_list
	while True:
		try:
			data = requests.get(url = url, timeout = 5)
			break
		except:
			pass
	data = data.content
	data = data.replace(codecs.BOM_UTF8,"")
	data = json.loads(data)
	data = data['data']

	print data['cname'],"finished"

	chapter_list[cid] = "<div class='chapter'><h1>"+data['cname'] + "</h1>" + data['content'] + "</div><mbp:pagebreak />"
	chapter_list[cid] = data['cname'] + "\n" + data['content']

def main():
	keywords = raw_input("\033[1;32;40mPlease tell me the keywords of the book you want:\033[0m")
	#keywords = "龙王传说"
	if "./" in keywords:
		print "hacker!"
		exit()
	ret = get_bookId(keywords)
	url = ret[0]
	keywords = ret[1]

	data = requests.get(url = url)
	data = data.content
	data = data.replace(codecs.BOM_UTF8,"")
	data = data.replace(",]", "]")
	data = data.replace(",}", "}")
	data = json.loads(data)
	printGreen("Wait for downloading ...")
	data = data['data']['list']
	filename = keywords + ".txt"

	global chapter_list
	chapter_list = {}
	tasks = []
	c = 0
	for i in data:
		for j in i['list']:
			tmp = j
			print j
			curl = url + str(tmp['id']) + ".html"
			task = Thread(target = sub_chapter,args = (curl, c,))
			c += 1
			task.start()
			tasks.append(task)
	for task in tasks:
		task.join()

	fp = open("./ebooks/" + filename, "w")

	keys = chapter_list.keys()
	keys.sort()
	for key in keys:
		fp.write(chapter_list[key])
	fp.close()

	tagname = raw_input("\033[1;32;40mPlease tell me the name of the book you want:\033[0m")
	if tagname == "":
		tagname = filename
	send_email("./ebooks/" + filename, tagname, ktconfig)

main()
#filename = "longwangchuanshuo.txt"
#send_email("./ebooks/" + filename, filename, ktconfig)