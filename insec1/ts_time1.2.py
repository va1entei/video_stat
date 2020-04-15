import sys
import os
import requests
import datetime
import pandas as pd
import argparse
import imutils
import time
import cv2
import csv
import pytz

TIME_LIM = 900
DEF_AREA = 500
REFERER = ""

OUTNAME = 'video_'  # default output file name
LOC = ""  # default save location

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": REFERER,
    "DNT": "1",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache"
}

try:
    path_to_insec = sys.argv[1]
    path_to_in = sys.argv[2]
    video_url = sys.argv[3]    

except IndexError:
    print("Usage:  path/to/insec path/to/in urlvideo")
    sys.exit(1)

retpo_name="noname"
for file in os.listdir(path_to_insec):
    if file.endswith(".repo"):
        retpo_name=file
if retpo_name == "noname":
    print("repo file not found")
    sys.exit()
retpo_name=os.path.splitext(retpo_name)[0]
logi_name="noname"
for file in os.listdir(path_to_insec):
    if file.endswith(".login"):
        logi_name=file
if logi_name == "noname":
    print("login file not found")
    sys.exit()
logi_name=os.path.splitext(logi_name)[0]

pass_name="noname"
for file in os.listdir(path_to_insec):
    if file.endswith(".pass"):
        pass_name=file
if pass_name == "noname":
    print("pass file not found")
    sys.exit()
pass_name=os.path.splitext(pass_name)[0]


def detect_motion(file_name):
#    max_rect = 0
    num1 = 0
    vs = cv2.VideoCapture(file_name)
    firstFrame = None
    while True:
        frame = vs.read()
        frame = frame[1]
        text = "Unoccupied"
        if frame is None:
            break                
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if firstFrame is None:
            firstFrame = gray
            continue
        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        for c in cnts:
            if cv2.contourArea(c) < DEF_AREA:
                continue
#            if cv2.contourArea(c) <= max_rect:
#                continue
#            max_rect = cv2.contourArea(c)
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        frameOrig = frame.copy()
        folder1 = path_to_in+file_name.split('-')[0]
        if not os.path.exists(folder1):
            os.mkdir(folder1)
            
        folder1 = folder1+"/"+file_name.split('-')[1]+"-"+file_name.split('-')[2].split('.')[0]
        if not os.path.exists(folder1):
            os.mkdir(folder1)
           
        filejpg=folder1+"/"+file_name.split('.')[0]+"_"+str(num1)+"_.jpg"
        while  os.path.exists(filejpg):
            num1 += 1
            filejpg=folder1+"/"+file_name.split('.')[0]+"_"+str(num1)+"_.jpg"
                
        cv2.imwrite(filejpg, frameOrig)
    vs.release()   
    return num1
    
def getSegs(m3):
    lines = m3.text.split('\n')
    segments = []
    for line in lines:
        if '.ts' in line:
            segments.append(line)
    return segments


def dumpSegs(initUrl, segments, path, append=False):
    with open(path, 'ab' if append else 'wb') as f:
        for segment in segments:
            segurl = initUrl + '/' + segment
            success = False
            while not success:
                try:
                    seg = requests.get(segurl, headers=HEADERS)
                    success = True
                except:
                    print('retrying...')
            f.write(seg.content)


if __name__ == "__main__":
    print("start")
    m3u8 = requests.get(video_url, headers=HEADERS)
    segments = getSegs(m3u8)
    url = '/'.join(video_url.split('/')[:-1])
    aa = []
    bb = []
    print("csv")
    fieldnames = ['data', 'time_start','time_stop','count_move','screen']
    file_csv='insec1/names.csv'
    if not os.path.exists(file_csv):
        with open(file_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)    
            writer.writeheader()
            writer.writerow({'data': '20200101', 'time_start': '010101',
                'time_stop':'010101','count_move':'0',
                'screen':'none' })
                
    df = pd.read_csv(file_csv)
    datanow = df['data'].tolist()
    datanum = datanow[-1]
    timenow = df['time_stop'].tolist()
    timenum = timenow[-1]  
    tzloc = pytz.timezone('Europe/Warsaw')
    
    for i in segments:
        valuetmp = datetime.datetime.fromtimestamp(int(i.split('.')[0])/1000,tzloc)      
        if int(datanum) > int(valuetmp.strftime('%Y%m%d')):
            continue
        if int(datanum) == int(valuetmp.strftime('%Y%m%d')):
            if int(timenum) > int(valuetmp.strftime('%H%M%S')):
                continue
                
        aa.append(int(i.split('.')[0])/1000)
        bb.append(i)
        if aa[-1] - aa[0] > TIME_LIM:
            print(bb)
            value = datetime.datetime.fromtimestamp(aa[0],tzloc)
            value2 = datetime.datetime.fromtimestamp(aa[-1],tzloc)
            file_video_name = value.strftime('%Y%m%d-%H%M%S')+value2.strftime('-%H%M%S')+".ts"
            dumpSegs(url, bb,file_video_name )
            out = detect_motion(file_video_name)
            print(out)
#pogoda 
            with open(file_csv, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({'data': value.strftime('%Y%m%d'), 'time_start':  value.strftime('%H%M%S'),
                    'time_stop':value2.strftime('%H%M%S'),'count_move':out,
                    'screen':'none' if out == 0 else file_video_name.split('.')[0]+".jpg"})

            os.remove(file_video_name)

            os.system("git config --global user.name \""+logi_name+"\"")
            os.system("git config --global user.email "+logi_name+"@github.com")
            os.system("git remote set-url origin https://"+logi_name+":"+pass_name+"@github.com/"+logi_name+"/"+retpo_name+".git")
            os.system("git checkout master")
            os.system("git add  insec1 "+path_to_in)
            os.system("git commit -m \"oinion csv files\"")
            os.system("git push origin master   ") 	
            
            aa = []
            bb = []
