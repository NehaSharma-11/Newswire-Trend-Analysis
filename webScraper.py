#!/usr/bin/env python

import sys
sys.setrecursionlimit(5000)

import requests
from datetime import datetime, timedelta
from dateutil import parser
from os import makedirs
from os.path import join
from urllib.parse import urljoin
from glob import glob
from bs4 import BeautifulSoup
import re
import operator

from operator import itemgetter   
from difflib import SequenceMatcher 
import matplotlib.pylab as plt
import shutil

daysGap = 7
args = sys.argv
start = datetime.today()
end = datetime.today() - timedelta(days=daysGap)
#print(len(args))
if len(args) > 3:
	print("Please provide start and end date in double quotes")
	raise ValueError("Incorrect date format for either or both start and end date")
if len(args)>1:
    try:
    	if args[1] != "":
    		start = parser.parse(args[1])
    except:
    	print("Can not parse start as date, Please provide in MM-DD-YYYY format")
    	raise
    end = start - timedelta(days=daysGap)

if len(args)>2:
	try:
		if args[2] != "":
			end = parser.parse(args[2])
	except:
		print("Can not parse end as date, Please provide in MM-DD-YYYY format")
		raise

#print("start",start)
#print("end",end)

if start == end:
	print("Start date and end date can not be same")
	raise ValueError("Provided same Start date and end date")
if start < end:
	temp = start
	start = end
	end = temp
if start > datetime.today():
	print("Start date can not be greater than today")
	raise ValueError("Provided start date can not be greater than today")
	


NW_BASE_URL = 'https://www.newswire.com/'
THE_IDX_URL = 'https://www.newswire.com/newsroom/page/'

#MAX_PAGE_NUM = 13
#INDEX_PAGES_DIR = 'index-pages'

WIRES_DIR = 'wires'
RESULT_DIR = 'result'
#makedirs(INDEX_PAGES_DIR, exist_ok=True)
makedirs(WIRES_DIR, exist_ok=True)
makedirs(RESULT_DIR, exist_ok=True)
pagenum = 1
inRange = True

while inRange:
    resp = requests.get(THE_IDX_URL+str(pagenum))
    #print("Downloaded", resp.url)
    soup = BeautifulSoup(resp.text,'lxml')
    mydivs = soup.findAll("div", {"class": "ni-container"})
    for d in mydivs:
	    timeDiv = d.find('time')
	    time = parser.parse(timeDiv.attrs['datetime']) 
	    #print(time>start)
	    if time > start:
	    	break
	    elif time < end:
	    	inRange = False
	    	break
	    a = d.find('a')
	    url = urljoin(NW_BASE_URL, a.attrs['href'])
	    #print("Download from.. ", url)
	    resp = requests.get(url)
	    fn = a.attrs['href'].replace('/','-').strip('-') + '.html'
	    full_fn = join(WIRES_DIR,fn)
	    #print("Saving to...\n", full_fn)
	    with open(full_fn,'w') as wf:
	        wf.write(resp.text)
    pagenum+= 1


def loc_Regex(sequence):
    pattern = r"\n\t\t\t(.*),(.*)\n\t\t\t(.*)\t\t\t\(Newswire.com\).*"
    matchObj = re.match(pattern,sequence.strip(' '), re.M|re.I)
    loc = ' '
    if matchObj:
    	loc = matchObj.group(1)
    	date = matchObj.group(3)
    if loc == ' ':
    	print(sequence)
    return loc

def cat_Regex(sequence):
    pattern = r"\nCategories\:\n(.*)"
    matchObj = re.match(pattern,sequence, re.M|re.I)
    catStr = ' '
    if matchObj:
    	catStr = matchObj.group(1)
    catStr = catStr.split(',')
    cat = []
    set1 = set()
    for c in catStr:
    	isRep = False
    	item = c.strip()
    	for s in set1:
    		if SequenceMatcher(None, item, s).ratio() > 0.6:
    			isRep = True
    	if isRep == False:
    		cat.append(item)
    		set1.add(item)
    return cat

def tag_Regex(sequence):
    pattern = r"\nTags\:\n(.*)"
    matchObj = re.match(pattern,sequence, re.M|re.I)
    tagStr = ' '
    if matchObj:
    	tagStr = matchObj.group(1)
    tagStr = tagStr.split(',')
    tag = []
    set1 = set()
    for t in tagStr:
    	isRep = False
    	item = t.strip().strip('#')
    	for s in set1:
    		if SequenceMatcher(None, item, s).ratio() > 0.6:
    			isRep = True
    	if isRep == False:
    		tag.append(item)
    		set1.add(item)
    return tag

wire_names = glob(join(WIRES_DIR,'*.html'))
loc_dict = {}
cat_dict = {}
tag_dict = {}

for fname in wire_names:
	#print("File= ",fname)
	with open(fname, 'r') as rf:
		txt = rf.read()
	soup = BeautifulSoup(txt,'lxml')
	#Finding location- assuming single location
	cont_div = soup.find("div", {"class": "html-content"})
	date_loc = cont_div.find("strong");
	loc = loc_Regex(date_loc.text)
	loc_dict[loc] = loc_dict.get(loc,0)+1
	#print("Added location ",loc)
	#finding categories & tags- assuming list
	cat_tag_divs = soup.findAll(lambda tag: tag.name == 'p' and tag.get('class') == ['mb-0'])
	#print("Len of CAT_LOC= ",len(cat_tag_divs))
	#category list
	i = 0 
	j = 0
	if (len(cat_tag_divs) == 2):
	    j = 1
	cat = cat_Regex(cat_tag_divs[i].text)
	for c in cat:
		cat_dict[c] = cat_dict.get(c,0)+1
	#	print("Added category ",c)
	tag = tag_Regex(cat_tag_divs[j].text)
	for t in tag:
		tag_dict[t] = tag_dict.get(t,0)+1
	#	print("Added tag ",t)

topLoc = sorted(loc_dict.items(), key=operator.itemgetter(1), reverse=True)
topLoc = topLoc[:min(len(topLoc),6)]
print("Trending Locations: ", topLoc)
x1,y1 = zip(*topLoc)
plt.plot(x1,y1)
plt.xticks(rotation=90)
plt.ylabel('Frequency')
plt.title('Trending Locations')
plt.subplots_adjust(bottom=0.45)
plt.savefig(join(RESULT_DIR,'Trending_Locations.png'))
plt.close()

topCat = sorted(cat_dict.items(), key=operator.itemgetter(1), reverse=True)
topCat = topCat[:min(len(topCat),6)]
print("Trending Categories: ",topCat)
x2,y2 = zip(*topCat)
plt.plot(x2,y2)
plt.xticks(rotation=90)
plt.ylabel('Frequency')
plt.title('Trending Categories')
plt.subplots_adjust(bottom=0.45)
plt.savefig(join(RESULT_DIR,'Trending_Categories.png'))
plt.close()

topTag = sorted(tag_dict.items(), key=operator.itemgetter(1), reverse=True)
topTag = topTag[:min(len(topTag),6)]
print("Trending Tags: ",topTag)
x3,y3 = zip(*topTag)
plt.plot(x3,y3)
plt.xticks(rotation=90)
plt.ylabel('Frequency')
plt.title('Trending Tags')
plt.subplots_adjust(bottom=0.45)
plt.savefig(join(RESULT_DIR,'Trending_KeyWords.png'))
plt.close()

shutil.rmtree(WIRES_DIR)