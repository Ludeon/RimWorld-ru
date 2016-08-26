# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET

path = r".\DefInjected"
pathAnother = r".\DefInjectedAnother"
pathKey = r".\Keyed"
pathKeyAnother = r".\KeyedAnother"

ex = [".label", ".rulesStrings", ".description", ".gerund", ".verb", ".deathMessage", ".pawnsPlural", ".fixedName", ".gerundLabel", ".pawnLabel", ".labelShort",
    ".labelSocial", ".stuffAdjective", ".labelMale", ".labelFemale", ".quotation", ".formatString", ".skillLabel", ".customLabel",
      ".text", ".name", ".summary", ".jobString", ".letterLabelFriendly", ".arrivalTextFriendly", ".successfullyRemovedHediffMessage",
      ".arrivalTextEnemy", ".letterLabelEnemy", ".labelMechanoids", ".recoveryMessage", ".inspectLine", ".beginLetter", ".beginLetterLabel",
      ".endMessage", ".adjective", ".reportString", ".letterLabel", ".letterText", ".graphLabelY", ".letter", ".oldLabel", ".labelSolidTended",
      ".labelSolidTendedWell", ".labelTendedInner", ".labelTendedWellInner", ".destroyedLabel", ".labelTended", ".labelTendedWell",
      ".destroyedOutLabel", ".destroyedLabel", ".discoverLetterText", ".discoverLetterLabel", ".leaderTitle"
          ]
ex2 = [".helpTexts.", ".rulesStrings."]

def compare(path, pathRus):
    #print u"Началось сравнение с %s"%path
    print path
    treeEng = ET.parse(path)
    rootEng = treeEng.getroot()
    listElements = [x.tag for x in rootEng]
    treeRus = ET.parse(pathRus)
    rootRus = treeRus.getroot()
    for elementRus in rootRus:
        tagRus = elementRus.tag
        ask = True
        countTag = len(tagRus)
        for x in ex:
            count = len(x)
            if countTag > count and tagRus[-count:] == x:
                ask = False
                break
        if(ask):
            for x in ex2:
                if x in tagRus:
                    ask = False
                    break
        if(ask):
            print tagRus
        if tagRus in listElements:
            if(listElements.count(tagRus) > 1):
                i = 1
                count = listElements.count(tagRus)
                while(i < count):
                    listElements.remove(tagRus)
                    i = i + 1
            listElements.remove(tagRus)
    if(listElements):
        print u"Файл: %s"%path
        print u"Следующие элементы отсутствуют у русской версии:"
        for element in listElements:
            print element
        print
    else:
        print u"Успешно\n"
    
def findXML(path, pathRus):
    listOfDir = os.listdir(path)
    for element in listOfDir:
        if ".xml" in element:
            xmlRus = os.path.join(pathRus, element)
            if os.path.isfile(xmlRus):
                compare(os.path.join(path, element), xmlRus)
            else:
                print u"У русской версии не существует файла %s\n"%xmlRus

listOfDir = os.listdir(pathAnother)
for element in listOfDir:
    sub = os.path.join(pathAnother, element)
    if os.path.isdir(sub):
        subRus = os.path.join(path, element)
        if os.path.exists(subRus):        
           findXML(sub, subRus)
        else:
           print u"У русской версии не существует папки %s"%subRus

#findXML(pathKeyAnother, pathKey)
