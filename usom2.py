#!/usr/bin/python3
import re, urllib.request
def regex():
 try:
  urllib.request.urlretrieve("https://www.usom.gov.tr/url-list.txt", r"/home/fatih/Desktop/usom.txt")
  ip=[]
  url=[]
  with open(r"/home/fatih/Desktop/usom.txt") as fh: 
   fstring = fh.readlines()
   for line in fstring:
    if re.findall(r'^\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b$',str(line)):
     ip.append(line)
    else:
     url.append(line)
  with open(r"/home/fatih/Desktop/ip_usom.txt","a") as ip_file: 
   for line in ip:
    ip_file.write(str(line) + "\n")   
  with open(r"/home/fatih/Desktop/url_usom.txt","a") as url_file:
   for line2 in url:
    url_file.write(str(line2) + "\n")    
 except ValueError:
  print("Hata oluştu!")
regex()
