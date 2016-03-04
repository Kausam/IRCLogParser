import os.path
import re
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import pylab
import pygraphviz as pygraphviz

log_directory = "/home/rohan/IRCLogParser_Files/2013/"
channel_name= "#kubuntu-devel" #channel name

startingMonth = 11
endingMonth = 12

rem_time= None #remembers the time of the last message of the file parsed before the current file

def correctLastCharCR(inText):
 #if the last letter of the nick is '\' replace it by 'CR' for example rohan\ becomes rohanCR to avoid complications in nx because of \
 if(inText[len(inText)-1]=='\\'):
  inText = inText[:-1]+'CR'
 return inText

for folderiterator in range(startingMonth, endingMonth + 1):
 for fileiterator in range(1,32):
  if(fileiterator<10):  
   filePath=log_directory+str(folderiterator)+"/0"+str(fileiterator)+"/"+channel_name+".txt"
  else:
   filePath=log_directory+str(folderiterator)+"/"+str(fileiterator)+"/"+channel_name+".txt"   
  if not os.path.exists(filePath):
   if not((folderiterator==2 and (fileiterator ==29 or fileiterator ==30 or fileiterator ==31)) or ((folderiterator==4 or folderiterator==6 or folderiterator==9 or folderiterator==11) and fileiterator==31 )): 
    print "[Error] Path "+filePath+" doesn't exist"
   continue 
  with open(filePath) as f:
      content = f.readlines() #contents stores all the lines of the file channel_name
    
  nicks = [] #list of all the nicknames
  send_time = [] #list of all the times a user sends a message to another user

  '''
   Getting all the nicknames in a list nicks[]
  '''
  for i in content:
   if(i[0] != '=' and "] <" in i and "> " in i):
    m = re.search(r"\<(.*?)\>", i)
    if m.group(0) not in nicks:                       
     nicks.append(m.group(0))   #used regex to get the string between <> and appended it to the nicks list

  for i in xrange(0,len(nicks)):
   nicks[i] = nicks[i][1:-1]     #removed <> from the nicknames
    
  for i in xrange(0,len(nicks)):
   nicks[i]=correctLastCharCR(nicks[i])

  for line in content:
   if(line[0]=='=' and "changed the topic of" not in line): #excluding the condition when user changes the topic. Search for only nick changes
    nick1=correctLastCharCR(line[line.find("=")+1:line.find(" is")][3:])
    nick2=correctLastCharCR(line[line.find("wn as")+1:line.find("\n")][5:])
    if nick1 not in nicks:
     nicks.append(nick1)
    if nick2 not in nicks:
     nicks.append(nick2)
   
  #print("printing nicks***********************************")
  #print(nicks)
    
  '''
   Forming list of lists for avoiding nickname duplicacy
  '''
  nick_same_list=[[] for i in range(len(nicks))] #list of list with each list having all the nicks for that particular person
  
  for line in content:
   if(line[0]=='=' and "changed the topic of" not in line): #excluding the condition when user changes the topic. Search for only nick changes
    nick1=correctLastCharCR(line[line.find("=")+1:line.find(" is")][3:])
    nick2=correctLastCharCR(line[line.find("wn as")+1:line.find("\n")][5:])
    for i in range(len(nicks)):
     if nick1 in nick_same_list[i]:
      nick_same_list[i].append(nick1)
      nick_same_list[i].append(nick2)
      break
     if not nick_same_list[i]:
      nick_same_list[i].append(nick1)
      nick_same_list[i].append(nick2)
      break

  #print("printing nick_same_list****************************")
  #print(nick_same_list)     

  '''=========================== Plotting the nickname changes graph =========================== '''

  graph_nickchanges=nx.MultiDiGraph()   #using networkx
  y=-1
  for i in content:
   y=y+1
   if(i[0] =='=' and "changed the topic of" not in i):  #excluding the condition when user changes the topic. Search for only nick changes
    nick1=correctLastCharCR(i[i.find("=")+1:i.find(" is")][3:])
    nick2=correctLastCharCR(i[i.find("wn as")+1:i.find("\n")][5:])
    z=y
    while z>=0:
     z=z-1
     if(content[z][0]!='='):
      graph_nickchanges.add_edge(nick1,nick2,weight=content[z][1:6])
      break                             # these lines extract the from-to nicknames and strip them appropriately to make 
    if(z==-1):
     graph_nickchanges.add_edge(nick1,nick2,weight=rem_time)                                            #edge between them  
  
  count=len(content)-1
  while(count>=0):
   if(content[count][0]!='='):
    rem_time=content[count][1:6]
    break
   count=count-1

  for u,v,d in graph_nickchanges.edges(data=True):
      d['label'] = d.get('weight','')

  output_dir=channel_name+"_"+str(fileiterator)+"_"+str(folderiterator)+"_2013_nickchanges.png"
  print(output_dir)
  A = nx.drawing.nx_agraph.to_agraph(graph_nickchanges)
  A.layout(prog='dot')
  A.draw(output_dir) #graphviz helps to convert a dot file to PNG format for visualization
  

  '''=========================== Plotting the conversation graph =========================== '''

  graph_conversation = nx.MultiDiGraph()  #graph with multiple directed edges between clients used
  for line in content:
   flag_comma = 0
   if(line[0] != '=' and "] <" in line and "> " in line):
    m = re.search(r"\<(.*?)\>", line)
    var = m.group(0)[1:-1]
    var = correctLastCharCR(var)
    for d in range(len(nicks)):
     if var in nick_same_list[d]:
      nick_sender = nick_same_list[d][0]
      break
     else:
      nick_sender = var
      
    for i in nicks:
     data=[e.strip() for e in line.split(':')]
     data[1]=data[1][data[1].find(">")+1:len(data[1])]
     data[1]=data[1][1:]
     if not data[1]:
      break
     for k in xrange(0,len(data)):
      if(data[k] and data[k][len(data[k])-1]=='\\'):
       data[k]=data[k][:-1]
       data[k]=data[k] + 'CR'
     for z in data:
      if(z==i):
       send_time.append(line[1:6])
       if(var != i):  
        for d in range(len(nicks)):
         if i in nick_same_list[d]:
          nick_receiver=nick_same_list[d][0]
          break
         else:
          nick_receiver=i
          
        graph_conversation.add_edge(nick_sender,nick_receiver,weight=line[1:6])  
       
     if "," in data[1]: 
      flag_comma = 1
      data1=[e.strip() for e in data[1].split(',')]
      for ij in xrange(0,len(data1)):
       if(data1[ij] and data1[ij][len(data1[ij])-1]=='\\'):
        data1[ij]=data1[ij][:-1]
        data1[ij]=data1[ij] + 'CR'
      for j in data1:
       if(j==i):
        send_time.append(line[1:6])
        if(var != i):   
         for d in range(len(nicks)):
          if i in nick_same_list[d]:
           nick_receiver=nick_same_list[d][0]
           break
          else:
           nick_receiver=i
          
         graph_conversation.add_edge(nick_sender,nick_receiver,weight=line[1:6])   

     if(flag_comma == 0):
      search2=line[line.find(">")+1:line.find(", ")] 
      search2=search2[1:]
      search=correctLastCharCR(search2)
      if(search2==i):
       send_time.append(line[1:6])
       if(var != i):
        for d in range(len(nicks)):
         if i in nick_same_list[d]:
          nick_receiver=nick_same_list[d][0]
          break
         else:
          nick_receiver=i
         
        graph_conversation.add_edge(nick_sender,nick_receiver,weight=line[1:6])  
      
  for u,v,d in graph_conversation.edges(data=True):
      d['label'] = d.get('weight','')
  output_dir=channel_name+"_"+str(fileiterator)+"_"+str(folderiterator)+"_2013_conversation.png"
  print(output_dir)
  A = nx.drawing.nx_agraph.to_agraph(graph_conversation)
  A.layout(prog='dot')
  A.draw(output_dir)