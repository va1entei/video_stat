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
import glob
from PIL import Image ,ImageDraw
import shutil



TIME_LIM = 600
DEF_AREA = 230
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
	
def funExFile(exfile,expath):
    nametm="noname"
    for file in os.listdir(expath):
        if file.endswith(exfile):
            nametm=file
    if nametm == "noname":
        print("file not found "+exfile)
        sys.exit()
    nametm=os.path.splitext(nametm)[0]
    return nametm
	


retpo_name=funExFile(".repo",path_to_insec)
logi_name=funExFile(".login",path_to_insec)
pass_name=funExFile(".pass",path_to_insec)

def detect_motion(file_name):
    flg_save = 0
    num1rect = 0
    siz1rect = 0
    step_sv = 0
    coun_save = 0
    capms = 1
    valueRoad=0
    maxRoad=0
    xLost=0
    yLost=0
    xRoad=0
    vs = cv2.VideoCapture(file_name)
    firstFrame = None
    while True:
        frame = vs.read()
        frame = frame[1]
        text = "Unoccupied"
        if frame is None:
            break      
        frame = imutils.resize(frame, width=500)	
        (ha, wa,c) =  frame.shape
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
        siz1rectloc = 0
        for c in cnts:
            if cv2.contourArea(c) < DEF_AREA:
                continue
            if cv2.contourArea(c) > siz1rect:
                siz1rect = cv2.contourArea(c)		
            if cv2.contourArea(c) > siz1rectloc:
                siz1rectloc = cv2.contourArea(c)
                (x1,y1,w1,h1) = cv2.boundingRect(c)
                if maxRoad<valueRoad:
                    maxRoad=valueRoad
                if xRoad==0:
                    xRoad=x1
                if abs(xLost-x1)>0 and abs(xLost-x1)<10 and abs(yLost-y1)<10: 
                    valueRoad =abs(xRoad-x1)
                elif abs(xLost-x1)>10 or abs(yLost-y1)>10:
                    xRoad=x1
                    valueRoad = 0
                xLost=x1
                yLost=y1
                
                if wa/w1 < 5:
                    w1=w1/5
                if ha/h1 < 5:
                    h1=h1/5
                transparent_area1 = (0,0,wa,y1)
                transparent_area2 = (0, y1 + h1,wa,ha)
                transparent_area3 = (0,y1, x1,y1 + h1)
                transparent_area4 = (x1+w1,y1, wa,y1 + h1)                
            if len(cnts) > num1rect:
                num1rect = len(cnts)
            
            flg_save += 1
            
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        if flg_save > 0:
            flg_save = 0
            frameOrig = frame.copy()
            
            folder1 = path_to_in+file_name.split('-')[0]
            if not os.path.exists(folder1):
                os.mkdir(folder1)
            
#            folder1 = folder1+"/"+file_name.split('-')[1]+"-"+file_name.split('-')[2].split('.')[0]
#            if not os.path.exists(folder1):
#                os.mkdir(folder1)
  
            filejpg=folder1+"/"+file_name.split('.')[0]+"_"+str(step_sv)+"_.jpg"
            if os.path.exists(filejpg):
                os.remove(filejpg)           

            coun_save += 1
            cv2.imwrite(filejpg, frameOrig)
            
            image1 = Image.open(folder1+"/"+file_name.split('.')[0]+"_0_.jpg")
            image2 = Image.open(filejpg)
            image1.putalpha(1)
            image2.putalpha(1)
            
            mask=Image.new('L', image2.size, color=255)
            draw=ImageDraw.Draw(mask) 
            draw.rectangle(transparent_area1, fill=0)
            draw.rectangle(transparent_area2, fill=0)
            draw.rectangle(transparent_area3, fill=0)
            draw.rectangle(transparent_area4, fill=0)
            image2.putalpha(mask)
            alphaComposited = Image.alpha_composite(image1, image2)

            rgb_im = alphaComposited.convert('RGB')
            rgb_im.save(folder1+"/"+file_name.split('.')[0]+"_0_.jpg")  
            if step_sv == 0:
                step_sv = 1
            elif os.path.exists(filejpg):
                os.remove(filejpg)    
        if capms != 0.0:
            capms = vs.get(cv2.CAP_PROP_POS_MSEC)
    
    vs.release()   
    return coun_save,capms,siz1rect,num1rect,maxRoad            
    
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
    now1 = datetime.datetime.now()
    if os.path.exists("README.md"):
        if not os.path.exists(now1.strftime('%Y%m%d')+".md"):
            os.rename("README.md", now1.strftime('%Y%m%d')+".md")
    fieldnames = ['data', 'time_start','time_stop','count_move','caps_num','size_rect','count_rect','screen']
    file_csv='insec1/names.1.4.csv'
    if not os.path.exists(file_csv):
        with open(file_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)    
            writer.writeheader()
            writer.writerow({'data': '20200101', 'time_start': '010101',
                'time_stop':'010101','count_move':'0','caps_num':'0.0',
                'size_rect':'0','count_rect':'0','screen':'none' })
                
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
        value = datetime.datetime.fromtimestamp(aa[0],tzloc)
        value2 = datetime.datetime.fromtimestamp(aa[-1],tzloc)
        if aa[-1] - aa[0] > TIME_LIM or value.strftime('%Y%m%d') != value2.strftime('%Y%m%d'):        
            #print(bb)
            file_video_name = value.strftime('%Y%m%d-%H%M%S')+value2.strftime('-%H%M%S')+".ts"
            dumpSegs(url, bb,file_video_name )
            out,caps_num,sizrect,numrect,maxRd = detect_motion(file_video_name)
            #print(out)
#pogoda 
            with open(file_csv, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({'data': value.strftime('%Y%m%d'), 'time_start':  value.strftime('%H%M%S'),
                    'time_stop':value2.strftime('%H%M%S'),'count_move':out,
                    'caps_num':caps_num,'size_rect':maxRd,'count_rect':numrect,
                    'screen':'none' if out == 0 else file_video_name.split('.')[0]+".jpg"})
            if out != 0:
                with open("README.md", 'a', newline='') as filemd:
#                ![20202020 1](in/20200426/000008-001013/20200426-000008-001013_0_.jpg)
#                    path_to_in+file_name.split('-')[0]+"/"+file_video_name.split('.')[0]+".jpg"
                    writerow1 = "!["+file_video_name.split('.')[0]+"]("+path_to_in+file_video_name.split('-')[0]+"/"+file_video_name.split('.')[0]+"_0_.jpg)\n"    
                    filemd.write(writerow1)
            if maxRd > 50 and numrect>0 and maxRd/numrect>2:
                os.rename(file_video_name,"/opt/video.mp4")
                os.system("(cd /opt/ && python3 -m youtube_video_upload ex.yaml)")
                os.remove("/opt/video.mp4")
            else:
                os.remove(file_video_name)

            os.system("git config --global user.name \""+logi_name+"\"")
            os.system("git config --global user.email "+logi_name+"@github.com")
            os.system("git remote set-url origin https://"+logi_name+":"+pass_name+"@github.com/"+logi_name+"/"+retpo_name+".git")
            os.system("git checkout master")
            os.system("git add  insec1 "+path_to_in+" *.md")
            os.system("git commit -m \"add .gif and .jpg  files\"")
            os.system("git push origin master   ") 	
            
            aa = []
            bb = []
		
    df = pd.read_csv(file_csv)			
    st1 = df['data'].unique()
    #print(st1)
    for file in os.listdir(path_to_in):
        if file in str(st1):
            continue
        #print(path_to_in+file)
        shutil.rmtree(path_to_in+file, ignore_errors=True)  
    for file in os.listdir("./"):
        if not file.endswith(".md"):
            continue
        if file == "README.md":
            continue
        print(file)
        dataout=os.path.splitext(file)[0]
        print(dataout)
        if dataout in str(st1):
            continue
        os.remove(file)
    os.system("git config --global user.name \""+logi_name+"\"")
    os.system("git config --global user.email "+logi_name+"@github.com")
    os.system("git remote set-url origin https://"+logi_name+":"+pass_name+"@github.com/"+logi_name+"/"+retpo_name+".git")
    os.system("git checkout master")
    os.system("git add  -A insec1 "+path_to_in+" *.md")
    os.system("git commit -am \"delete file in no in csv\"")
    os.system("git push origin master   ") 
