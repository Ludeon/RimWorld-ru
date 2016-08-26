# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET
import re

pathOriginal = r".\Defs"
pathRus = r".\DefInjected"
pathRusOrg = r".\DefInjectedRaws"

path = r".\Defs\ThoughtDefs\Thoughts_Situation_RoomStats.xml"

tagText = ["label", "rulesStrings", "description", "gerund", "verb", "deathMessage", "pawnsPlural", "fixedName", "gerundLabel", "pawnLabel", "labelShort",
    "labelSocial", "stuffAdjective", "labelMale", "labelFemale", "quotation", "formatString", "skillLabel", "customLabel",
      "text", "name", "summary", "jobString", "letterLabelFriendly", "arrivalTextFriendly", "successfullyRemovedHediffMessage",
      "arrivalTextEnemy", "letterLabelEnemy", "labelMechanoids", "recoveryMessage", "inspectLine", "beginLetter", "beginLetterLabel",
      "endMessage", "adjective", "reportString", "letterLabel", "letterText", "graphLabelY", "letter", "oldLabel", "labelSolidTended",
      "labelSolidTendedWell", "labelTendedInner", "labelTendedWellInner", "destroyedLabel", "labelTended", "labelTendedWell",
      "destroyedOutLabel", "destroyedLabel", "discoverLetterText", "discoverLetterLabel", "leaderTitle", "helpTexts", "rulesStrings",
           "instantlyOldLabel", "useLabel", "ingestCommandString", "ingestReportString"
          ]
allText = {}
allTextValue = {}
pathsOfNewXML = {}
pathsOfXML = {}

def addElement(fileXML, elementText, text):
    if("subSounds" not in elementText):
        if(fileXML not in allText):
            allText.update([(fileXML, [])])
        elementsList = allText[fileXML]
        if(elementText not in elementsList):
            elementsList.append(elementText[:])
            allTextValue.update([(elementText, text)])

def findText(element, tagPath, li, fileXML):
    for subElement in element:
        if(subElement.tag in tagText):
            countSubElement = list(subElement)
            if(countSubElement):
                i = 0
                tagPathSub = tagPath + "." + subElement.tag
                for sub2Element in subElement:
                    text = sub2Element.text
                    if(text):
                        addElement(fileXML, tagPathSub + u"." + str(i), text)
                    i = i + 1
            else:
                text = subElement.text
                if(text):            
                    addElement(fileXML, tagPath + u"." + subElement.tag, text)
        else:
            listElement = list(subElement)
            isli = subElement.tag == "li"
            if(listElement):
                if(isli):
                    findText(subElement, (tagPath + u"." + str(li))[:], 0, fileXML)
                else:
                    findText(subElement, (tagPath + u"." + subElement.tag)[:], 0, fileXML)
            if(isli):
                li = li + 1
            text = subElement.text
            if(text):
                expectSTR = re.compile(u"[a-z]+")
                result = expectSTR.match(text)
                if(result and text != u"false" and text != u"true"):
                    print tagPath + u"." + subElement.tag + u" значение:"
                    print text

def gather(path, fileXML):
    tree = ET.parse(path)
    root = tree.getroot()
    for element in root:
        defName = element.find("defName")
        if(defName is None):
            defName = element.find("DefName")
        if(defName is not None):
            tagPath = defName.text
            findText(element, tagPath, 0, fileXML)
        else:
            classAbs = element.get("Name")
            print u"Внимание! Абстрактный класс %s\n"%classAbs
            if(classAbs):
                tagPath = classAbs
            else:
                tagPath = "None"
            findText(element, tagPath, 0, fileXML)
    
def compare(path, listElementsText):
    tree = ET.parse(path)
    root = tree.getroot()
    for element in root:
        if(element.tag in listElementsText):
            listElementsText.remove(element.tag)
    
def findXMLORG(path):
    listOfDir = os.listdir(path)
    for fileXML in listOfDir:
        if ".xml" in fileXML:
            (head, tail) = os.path.split(path)
            pathNewXML = os.path.join(pathRusOrg, tail)
            pathsOfNewXML[fileXML] = os.path.join(pathNewXML, fileXML)
            gather(os.path.join(path, fileXML), fileXML)
        else:
            subDir = os.path.join(path, fileXML)
            if os.path.isdir(subDir):
                findXMLORG(subDir)

def findXMLRUS(path):
    listOfDir = os.listdir(path)
    for fileXML in listOfDir:
        if ".xml" in fileXML:
            if fileXML in allText:
                pathXML = os.path.join(path, fileXML)
                pathsOfXML[fileXML] = pathXML
                compare(os.path.join(path, fileXML), allText[fileXML])
            else:
                print u"Отсуствует файл %s в исходных defs"%fileXML                

def proofFile(path):
    tree = ET.parse(path)
    root = tree.getroot()
    element = root.find("ThoughtDef/stages")
    i = 0
    for sub in element:
        label = sub.find("label")
        print sub.tag == "li"
        print sub.tag
        if(label is not None):
            print label.text
        print i
        i = i + 1
        

listOfDir = os.listdir(pathOriginal)
for element in listOfDir:
    sub = os.path.join(pathOriginal, element)
    if os.path.isdir(sub): 
        findXMLORG(sub)

listOfDir = os.listdir(pathRus)
for element in listOfDir:
    sub = os.path.join(pathRus, element)
    if os.path.isdir(sub): 
        findXMLRUS(sub)

for key in allText.keys():
    if key not in pathsOfXML:
        print u"\nОтсуствует файл для перевода %s\n"%key
    allElement = allText[key]
    if(allElement):
        print u"\nВ файле %s отсутствует:"%key
        for element in allElement:
            print u"%s значение: %s"%(element, allTextValue[element])

for key in allText.keys():
    allElement = allText[key]
    if(allElement):
        if(key in pathsOfXML):
            #parse must use encode utf-8
            tree = ET.parse(pathsOfXML[key])
            root = tree.getroot()
        else:
            tree = ET.ElementTree()
            newRoot = ET.Element("LanguageData")
            tree._setroot(newRoot)
            root = tree.getroot()
        if(key in pathsOfNewXML):
            path = pathsOfNewXML[key]
            (head, tail) = os.path.split(path)
            if(not os.path.exists(head)):
                os.makedirs(head)
        else:
            path = os.path.join(pathRusOrg, key)
        for element in allElement:
            #newElement = ET.Element(element)
            #newElement.text = allTextValue[element]
            #root.append(newElement)
            subElement = ET.SubElement(root, element)
            subElement.text = allTextValue[element]
        tree.write(path, encoding="utf-8", xml_declaration=True)        
