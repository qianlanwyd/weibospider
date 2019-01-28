#!/usr/bin/env python
# coding=utf-8

import requests
import bs4
import json
import re
import random
import csv
import time
import socket
import traceback
import urllib.request

headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}
total_number = 0
#https://m.weibo.cn/api/container/getIndex?type=uid&value=1280761142&containerid=1076031280761142
#url = 'http://m.weibo.cn/u/1280761142'
num = 0
ip_list = []
save_list =[]
url_list = []
oid = ''
oidlist=['3937348351','2803301701','1699432410','2656274875','1618051664','2028810631','5476386628']
weibo_url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value='+oid
weibo_list = ''
flag=True
def use_proxy(url,proxy_addr):
	req=urllib.request.Request(url)
	req.add_header("User-Agent","Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0")
	proxy=urllib.request.ProxyHandler({'http':proxy_addr})
	opener=urllib.request.build_opener(proxy,urllib.request.HTTPHandler)
	urllib.request.install_opener(opener)
	data=urllib.request.urlopen(req).read().decode('utf-8','ignore')
	return data
def get_containerid(url):
	proxy_addr=get_random_ip()
	data=use_proxy(url,proxy_addr)
	content=json.loads(data).get('data')
	for data in content.get('tabsInfo').get('tabs'):
		if(data.get('tab_type')=='weibo'):
			containerid=data.get('containerid')
			return containerid

def get_ip_list(url):
	global ip_list
	web_data = requests.get(url, headers=headers)
	soup = bs4.BeautifulSoup(web_data.text, 'lxml')
	ips = soup.find_all('tr')
	for i in range(1, len(ips)):
		ip_info = ips[i]
		tds = ip_info.find_all('td')
		ip_list.append(tds[1].text + ':' + tds[2].text)


def get_random_ip():
	proxy_list = []
	for ip in ip_list:
		proxy_list.append('http://' + ip)
	proxy_ip = random.choice(proxy_list)
	proxies = {'http': proxy_ip}
	return proxies

# selenium

def get_html(url):
	try:
		r= requests.get(url,headers=headers)
		soup = bs4.BeautifulSoup(r.text,'lxml')
		#如果状态码不是200，发出HTTOERROR
		r.raise_for_status()
		#设置正确的编码方式
		r.encoding = r.apparent_encoding#r.encoding = 'utf-8'
		return r.json()
	except:
		flag=False
		return "Something Wrong!"
def save_weibo(text):

	title_csv = ['发表时间','博文','点赞数量','评论数量','转发数量','博文链接']
	filename="data.csv"
	with open(filename,"w",newline ='') as csvfile:
		weibo_csv = csv.writer(csvfile)
		#weibo_csv.writerow(title_csv)
		print('here')
		print(len(save_list))
		for weibo in save_list:
			text=[]
			text.append(weibo['发表时间'])
			text.append(weibo['博文'])
			text.append(weibo['点赞'])
			text.append(weibo['评论'])
			text.append(weibo['转发'])
			text.append(weibo['博文链接'])
			weibo_csv.writerow(text)
	'''
	 with open('刘雯weibo.txt','a') as f:
		for txt in text:
			f.write(txt)
		f.close()
	'''

def get_content(url):
	url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + oid
	global total_number,num,save_list
	resp_data = get_html(url)
	url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + oid
	containerid = get_containerid(url)
	global weibo_list
	weibo_list = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + oid + '&containerid=' + containerid
	if flag is False:
		return
	userInfo = resp_data['data']['userInfo']
	total_number=userInfo['statuses_count']
	name = userInfo['screen_name']
	time_flag=True
	print(total_number)
	print(name)
	texts_url = []
	max_num = (int)(total_number/10)
	for i in range(1,max_num+1):
		temp = weibo_list+'&page=' + str(i)
		texts_url.append(temp)
	data = {
		'Referer':'https://m.weibo.cn/u/'+oid,
		}
	try:
		for text_url in texts_url:
			if time_flag is False:
				return
			print(text_url)
			proxies = get_random_ip()
			print(proxies)
			# 超时重连
			state = False
			timeout = 3
			socket.setdefaulttimeout(timeout)
			while not state:
				time.sleep(3)
				try:
					r = requests.get(text_url,headers=headers,data=data,proxies=proxies)
					state = True
				except socket.timeout:
					time.sleep(5*60)
					print("超时重连")
					state = False
					proxies = get_random_ip()
					print(proxies)
			text_data = r.json()
			text_cards = text_data['data']['cards']

			for text_info in text_cards:
				text={}
				#print(text_info)
				text_type = text_info["card_type"]
				if text_type != 9:
					continue
				text['博文链接'] = text_info['scheme']
				text_mblog = text_info['mblog']
				#print(text_mblog)

				num=num+1
				#处理博文
				text_dirty = text_mblog['text']
				try:
					clean1 = re.sub(r"<span.*?</span>",'',text_dirty)
					text_dirty = re.sub(r'<a.*?</a>','',clean1)
				except:
					print("无span链接")
					text_dirty = re.sub(r'<a.?*</a>','',text_dirty)
				pat=re.compile(r'[^\u4e00-\u9fa5]')#删除非中文字符 括号之类的
				text_dirty = pat.sub('',text_dirty)
				text['博文'] = text_dirty.strip()

				# 获取时间
				text['发表时间'] = text_mblog['created_at']
				if('2017' in text['发表时间']):
					time_flag=False
					break
				save_flag=False
				if('2018' in text['发表时间'] or str(text['发表时间']).count('-')==1):
					save_flag=True
				if(str(text['发表时间']).count('-')==1):
					text['发表时间']='2019-'+ text['发表时间']
				text['转发'] = text_mblog['reposts_count']
				text['评论'] = text_mblog['comments_count']
				text['点赞'] = text_mblog['attitudes_count']

				# 博文是否有图片
				#print(text['博文'],end='\t')
				#print(text['发表时间'])
				if(save_flag is True):
					save_list.append(text)
					save_weibo(text['博文'])
					#save_list.append(text['博文'])
			print("获取"+str(num)+"条博文...")
			# print(text_data)
	except Exception as e:
		print("Error:", e)
		traceback.print_exc()
		time.sleep(5*60)
def main():

	get_ip_list('http://www.xicidaili.com/nn/')
	print(oid)
	#print(proxies)
	try:
		get_content(weibo_url)
	except Exception as e:
		print("Error:", e)
		traceback.print_exc()
		#save_weibo(text)



if __name__ == '__main__':
	for i in range(0,len(oidlist)):
		#time.sleep(60*30)
		#save_list.clear()
		oid=oidlist[i]
		main()
		#print(oid)
