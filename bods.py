from datetime import datetime
from datetime import timedelta
from System.Collections.Generic import List
import re
import os
import math
import time

from System import Byte
import pickle

today = datetime.now()
dataFileLocation = "Data/bod.pkl"
dataNpcFileLocation = "Data/bodnpc.pkl"
stringWaitForBod = "An offer may be available"
gmpId = 777666
#dateStandard = "%m/%d %H:%M" #soccer means kicking ball
dateStandard = "%d/%m %H:%M" #football means kicking ball

def toSeconds(date):
    return time.mktime(date.timetuple()) 

def readData():
    try:
        with open(dataFileLocation, 'rb') as fp:
            ret = pickle.load(fp)
        return ret;
    except IOError:
        return {};
    
def writeData(data):
    with open(dataFileLocation, 'wb') as fp:
        pickle.dump(data, fp)
        
def readNpcData():
    try:
        with open(dataNpcFileLocation, 'rb') as fp:
            ret = pickle.load(fp)
        return ret;
    except IOError:
        return {};
    
def writeNpcData(data):
    with open(dataNpcFileLocation, 'wb') as fp:
        pickle.dump(data, fp)
            
def lookForTimer(createTimer = True, clearAfter = True):
    journalText = Journal.GetLineText(stringWaitForBod, True)
    journalList = journalText.split(":")
    if (len(journalList)>1):
        if createTimer:
            Timer.Create(journalList[0],60*1000)
        if clearAfter:
            Journal.Clear(Journal.GetLineText(stringWaitForBod))
        return journalList
    return False
    
def cleanUpJournal():
    journalText = Journal.GetLineText(stringWaitForBod, True)
    journalList = journalText.split(":")
    if (len(journalList)>1):
        Journal.Clear(Journal.GetLineText(stringWaitForBod))
        return True
    return False
        
def getNpcByName(npcName, range = 15):
    enemyFilter = Mobiles.Filter()
    enemyFilter.Enabled = True
    enemyFilter.RangeMin = 0
    enemyFilter.RangeMax = range
    enemyFilter.Notorieties = List[Byte](Byte(7))
    enemyFilter.CheckIgnoreObject = True
    enemyFilter.Name = npcName
    enemies = Mobiles.ApplyFilter( enemyFilter )
    if len(enemies)>0:
        return enemies[0]
        
def calculateTimeDiffInMinutes(tstamp1, tstamp2):
    tstamp1 = toSeconds(tstamp1) #conv to timestamp
    tstamp2 = toSeconds(tstamp2)
    if tstamp1 > tstamp2:
        td = tstamp1 - tstamp2
    else:
        td = tstamp2 - tstamp1
    return int(round(td / 60))
    
def calculateNumberOfReadyBods(timeChecked, timeRemaining):
    timediff = calculateTimeDiffInMinutes(timeChecked, datetime.now())
    deedswaitingFloat = (timediff - timeRemaining) / 360
    return int(math.floor(deedswaitingFloat)+1)
    
def fixDoublingNpcs(npcName):
    npcName = re.sub('\ guildmaster$', '', npcName)
    npcName = re.sub('\ guildmistress$', '', npcName)
    if npcName == 'weaver':
        return 'tailor'
    if npcName == 'weaponsmith':
        return 'blacksmith'
    if npcName == 'armorer':
        return 'blacksmith'
    return npcName
    
def handleBodGump(timeout = False):
    gumpFarm = 150663902
    gumpFarmOther = 3788093160
    gumpTamer = 364681892
    gumpNormalBod = 2611865322
    gumpCook = 3188567326
    gumpsBods = [gumpFarm, gumpFarmOther, gumpTamer, gumpNormalBod, gumpCook]
    if timeout:
        Timer.Create('bod gump timeout', timeout)#timeout
    foundGump = 999911115555 #timeout, default value. hope no gump uses it
    for gumpBod in gumpsBods:
        Misc.Pause(100)
        if Gumps.HasGump(gumpBod):
            Gumps.SendAction(gumpBod, 1)
            Misc.Pause(500)
            #cleanup, uo for some reasons keeps gumps open after we click them
            Gumps.CloseGump(gumpBod)
            return True
    if timeout:
        remaining = Timer.Remaining('bod gump timeout')
        if remaining > 0:
            return False
    handleBodGump(timeout) #cursed :D 
      
    

def renderGump(timers):
    gd = Gumps.CreateGump(movable=True,closable=True,resizeable=True)
    Gumps.CloseGump(gmpId)
    Gumps.AddPage(gd,0)
    Gumps.AddBackground(gd, 0, 0, 370, 180, 30546)
    Gumps.AddAlphaRegion(gd,0,0,370,180)
    Gumps.AddLabel(gd,0,0,5, 'type')
    
    Gumps.AddLabel(gd,0,16,5, '------------------------------------------------------------')
    posx = 0
    posy = 32
    secondRow = 90
    thirdRow = 170
    fourthRow = 260
    fifthRow = 310
    Gumps.AddLabel(gd,posx + secondRow,0,5, '| nmb ready')
    Gumps.AddLabel(gd,posx + thirdRow,0,5, '| visited')
    Gumps.AddLabel(gd,posx + fourthRow,0,5, '| bod in')
    Gumps.AddLabel(gd,posx + fifthRow,0,5, '| all in')
    for itemKey,itemValue in timers.items():
        Gumps.AddLabel(gd,posx,posy,5, itemKey)
        Gumps.AddLabel(gd,posx + secondRow,posy,5, "| ")
        numberOfReadyBods = calculateNumberOfReadyBods(itemValue['timeChecked'], itemValue['time'])
        for i in range(numberOfReadyBods):
            Gumps.AddItem(gd,posx + secondRow + (i*20),posy,0x2DB1)
            #Gumps.AddItem(gd,x,y,itemID,hue)
        
        Gumps.AddLabel(gd,posx + thirdRow,posy,5, "| " + itemValue['timeChecked'].strftime(dateStandard))
        readyAtColor = 5
        readyMinutes = itemValue['time']
        readyAt = itemValue['timeChecked'] + timedelta(minutes=readyMinutes)
        readyNext = readyAt - datetime.now()
        readyNextColor = 5
        for i in range(1): # second bod and third bod
            if readyNext < timedelta(minutes=0):
                readyNext = readyNext + timedelta(minutes=360)
            if i == 1:
                readyNextColor = 22
        if readyNext < timedelta(minutes=0):
                readyNextColor = 38
                readyNext = timedelta(minutes=0)
        readyLast = readyAt - datetime.now() + (2*timedelta(minutes=360))
        readyLastColor = 5
        if readyLast < timedelta(minutes=0):
                readyLastColor = 38
                readyLast = timedelta(minutes=0)
        Gumps.AddLabel(gd,posx + fourthRow,posy,5, "| ")
        Gumps.AddLabel(gd,posx + fourthRow+10,posy,readyNextColor,':'.join(str(readyNext).split(':')[:2]))
        Gumps.AddLabel(gd,posx + fifthRow,posy,5, "| ")
        Gumps.AddLabel(gd,posx + fifthRow+10,posy,readyLastColor,':'.join(str(readyLast).split(':')[:2]))
        posy = posy + 16
        
    
    Gumps.SendGump(gmpId, Player.Serial, 25, 50, gd.gumpDefinition, gd.gumpStrings)


bodTimers = readData()
bodNpcs = readNpcData()
renderGump(bodTimers)
Timer.Create('refreshTimer',1*60*1000)
while cleanUpJournal():
    Misc.Pause(100) #clean up from bod messages. leave rest of messages alone
    
Misc.SendMessage("BOD helper is running. Here's list of NPC's that I know of:")
npcListToPrint = ""
for key, value in bodNpcs.items():
    npcListToPrint = npcListToPrint + key + ", "

Misc.SendMessage(npcListToPrint[:-2])
Misc.SendMessage("To teach me about NPC, just take all his BODs 4 times (untill he tells you the cooldown time)")
while True:
    if not Timer.Check('refreshTimer'):
        renderGump(bodTimers)
        Timer.Create('refreshTimer',1*60*1000) 
    for key, value in bodNpcs.items():
        who = getNpcByName(value, 2)
        if who and not Timer.Check(value):
            Misc.WaitForContext(who.Serial, 1000)
            if key.split(" the ")[1] == "animal trainer":
                Misc.ContextReply(who.Serial, 4)
            else:
                Misc.ContextReply(who.Serial, 1)
            Misc.Pause(500)
            if not lookForTimer(createTimer = False, clearAfter = False):
                handleBodGump(2000)
            Misc.Pause(500)
    
    jurnal = lookForTimer()
    if jurnal is not False:
        if jurnal[0] is not None:
            npcName = getNpcByName(jurnal[0])
            if npcName is not None:
                npcFullName = str(getNpcByName(jurnal[0]).Properties[0])
                npc = npcFullName.replace(jurnal[0],"")
                npc = npc.replace(" the ","")
                npc = npc.strip()
                npc = fixDoublingNpcs(npc)
                bodTimer = int(re.search(r'\d+', jurnal[1]).group())
                bodTimers[npc] = {}
                bodTimers[npc]['name'] = jurnal[0]
                bodTimers[npc]['time'] = bodTimer
                bodTimers[npc]['timeChecked'] = datetime.now()
                writeData(bodTimers)
                renderGump(bodTimers)
                if npcFullName not in bodNpcs:
                    bodNpcs[npcFullName] = bodTimers[npc]['name'] #ya, key = val. pickle returns dict not list
                    writeNpcData(bodNpcs)
    Misc.Pause(1000)