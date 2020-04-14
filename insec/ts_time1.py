import sys
import os
import requests
import datetime
#from imutils.video import VideoStream
import argparse
import imutils
import time
import cv2
import csv

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
    video_url = sys.argv[2]    

except IndexError:
    print("Usage:  path/to/insec")
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
    max_rect = 0
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
            if cv2.contourArea(c) <= max_rect:
                continue
            max_rect = cv2.contourArea(c)
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            frameOrig = frame.copy()
            filejpg="in/"+file_name.split('_')[1].split('.')[0]+".jpg"
            if os.path.exists(filejpg):
                os.remove(filejpg)
            cv2.imwrite(filejpg, frameOrig)
    vs.release()   
    return max_rect
    
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
    DEST = LOC + OUTNAME
    SOURCE = video_url
    delim = ''
    if '\\' in DEST:
        delim = '\\'
    elif '/' in DEST:
        delim = '/'
    if delim:
        PATH = ''.join(DEST.split(delim)[:-1])
        if not os.path.isdir(PATH):
            print('INAVLID DESTINATION.')
            sys.exit(0)
    print("request")
    m3u8 = requests.get(SOURCE, headers=HEADERS)
    segments = getSegs(m3u8)
    url = '/'.join(SOURCE.split('/')[:-1])
    aa = []
    bb = []
    print("csv")
    fieldnames = ['data', 'time_start','time_stop','count_move','screen']
    file_csv='insec/names.csv'
    if not os.path.exists(file_csv):
        with open(file_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)    
            writer.writeheader()

    for i in segments[500:]:
        aa.append(int(i.split('.')[0])/1000)
        bb.append(i)
        if aa[-1] - aa[0] > TIME_LIM:
            print(bb)
            value = datetime.datetime.fromtimestamp(aa[0])
            value2 = datetime.datetime.fromtimestamp(aa[-1])
            file_video_name = DEST+value.strftime('%Y%m%d-%H%M%S')+value2.strftime('-%H%M%S')+".ts"
            dumpSegs(url, bb,file_video_name )
            out = detect_motion(file_video_name)
            print(out)
#pogoda 
            with open(file_csv, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({'data': value.strftime('%Y%m%d'), 'time_start':  value.strftime('%H%M%S'),
                    'time_stop':value2.strftime('%H%M%S'),'count_move':out,
                    'screen':'none' if out == 0 else file_video_name.split('_')[1].split('.')[0]+".jpg"})

            os.system("git config --global user.name \""+logi_name+"\"")
            os.system("git config --global user.email "+logi_name+"@gmil.com")
            os.system("git remote set-url origin https://"+logi_name+":"+pass_name+"@github.com/"+logi_name+"/"+retpo_name+".git")
            os.system("git checkout master")
            os.system("git add in insec")
            os.system("git commit -m \"oinion csv files\"")
            os.system("git push origin master   ") 	
            
            aa = []
            bb = []
            os.remove(file_video_name)

