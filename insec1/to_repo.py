import pandas as pd
import sys
import yaml
import os
import shutil

try:
    path_to_insec = sys.argv[1]
    path_out = sys.argv[2]
except IndexError:
    print("Usage:  path/insec path/clean")
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




os.system("git config --global user.name \""+logi_name+"\"")
os.system("git remote set-url origin https://"+logi_name+":"+pass_name+"@github.com/"+logi_name+"/"+retpo_name+".git")
os.system("git checkout master")
os.system("git add "+path_out)
os.system("git commit -m \"oinion csv files\"")
os.system("git push origin master   ") 	
