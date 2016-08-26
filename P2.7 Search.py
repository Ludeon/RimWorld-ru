# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET
import re

ignoreWords = [u'\\n', u'art_name->', u'Wiki', u'OK', u'defs', u'assets', u'DPS', u'RimWorld', u'HIS', u'HISCAP', u'Steam', u'exoticname->',
                u'HE', u'NAME', u'ESC', u'CAP', u'HIM', u'vs.', u'WASD', u'PageUp', u'PageDown', u'TargetA',
                u'logentry->', u'desc_sentence->', u'circumstance_phrase->', u'[pawn_nameFull]',
                u'[project_label]', u'[circumstance_group]', u'desc_sentence->', u'[pawn_nameShortDef]', u'tale_noun->',
                u'[thing_label]', u'quality_sentence->', u'[pawn_possessive]', u'title_sentence->', u'[thing_labelDefinite]',
                u'[thing_title]', u'[thing_quality]', u'[human_nameShortDef]', u'[animal]', u'train_syn->', u'[animal_nameShortDef]',
                u'[prisoner_nameShortDef]', u'[killer_nameShortDef]', u'[victim_nameShortDef]', u'[killer_nameFull]',
                u'[item_labelDefinite]', u'[pawn_pronoun]', u'[pawn_objective]', u'[thing_labelIndefinite]', u'[quality_sentence]',
                u'[title_sentence]', u'[eat_gerund]', u'nude_action->', u'eat_gerund->', u'[item_labelDefinite]', u'[nude_action]',
                u'[outlander]', u'[terrainfeature]', u'[firstPawn_nameShortDef]', u'[secondPawn_nameShortDef]', u'image->[firstPawn_nameFull]',
                u'[secondPawn_nameFull]', u'[anima_possessive]', u'image->[human_nameFull]', u'[animal_nameFull]', u'[animal_ShortDef]',
                u'[quantity]', u'[color]', u'[vegetable]', u'image->[human_nameFull]', u'[trainable_label]', u'[animal_nameFull]',
                u'name->', u'physical_description_root->', u'[depiction]', u'[kidnapper_nameFull]', u'[warden_nameShortDef]',
                u'[image]', u'[desc_sentence_group]', u'sculpture->', u'[train_syn]', u'[seller_nameShortDef]', u'[trader_nameShortDef]',
                u'[trader_nameShortDef]', u'[prisoner_possessive]', u'image->', u'[seller_nameFull]', u'[prisoner_nameFull]',
                u'[capturer_nameShortDef]', u'[trader_nameFull]', u'[killer_pronoun]', u'[side_position]', u'[quantity_adjphrase]',
                u'[victim_nameFull]', u'[badassanimal]', u'[animalnameunisex]', u'[kidnapper_nameShortDef]', u'[victim_pronoun]',
                u'[prisoner_pronoun]', u'[warden_nameFull]', u'[kidnapper_factionName]', u'[patient_nameShortDef]', u'[surgeon_nameShortDef]',
                u'[patient_pronoun]', u'[surgeon_nameFull]', u'[patient_nameFull]', u'[prey_nameShortDef]', u'[hunter_nameShortDef]',
                u'[hunter_nameFull]', u'[prey_nameFull]', u'[joiner_nameShortDef]', u'[recruiter_nameFull]', u'[joiner_nameFull]',
                u'[capturer_nameFull]', u'rareseed->', u'[community]', u'[businessseed]', u'[game]', u'[weapon]', u'seed->',
                u'[joiner_pronoun]', u'[prisoner_objective]', u'[businesstype]', u'[rareseed]', u'[tribalword]', u'[concept]',
                u'[adjective]', u'[apparel]', u'[personseedfemale]', u'[personseedmale]', u'[celestialname]', u'[celestialsuffix]',
                u'[romannumeral]', u'[businesstype]', u'[letter]', u'[businessname]', u'[story]', u'[trans]', u'rule->', u'[positiveconcept]',
                u'[celestialprefix]', u'[colonyname]', u'[badassconcept]', u'[groupname]', u'[badassadjective]', u'[badassperson]',
                u'[badasscolor]', u'[exoticname]', u'[personnamefemale]', u'[animalnamefemale]', u'[animalnamemale]', u'sent->',
                u'[recipient_nameShortDef]', u'[personnamemale]', u'[initiator_nameShortDef]', u'[recipient_pronoun]', u'trans->',
                u'quantity_adjphrase->', u'[depicts]', u'[sculpture]', u'[angstyadjective]', u'[anyPawn_nameShort]', u'[angstyadjective]',
                u'[digit]', u'[artname]', u'subject_desc->', u'[angstyadjective]', u'[art_adjective]', u'[personname]', u'[subject_desc]',
                u'side_position->', u'[angstyconcept]', u'idle_verb_progressive->', u'artstyle_adj->', u'composition->', u'depiction->',
                u'depicts->', u'style_clause->', u'[composition]', u'[artstyle_adj]', u'artextra_clause->', u'[idle_verb_progressive]',
                u'style_group->', u'[style_clause]', u'[artextra_clause]', u'[style_group]', u'desc_sentence_group->', u'art_description_root->',
                u'[physical_description_root]', u'[context_sentence]', u'[tale_noun]', u'[date]', u'context_sentence->', u'circumstance_group->',
                u'[circumstance_phrase]', u'TargetB', u'[other_nameShortIndef]', u'[desc_sentence]'
               ]

def findChar(path, ignoreWords):
    print u"Поиск в %s"%path
    tree = ET.parse(path)
    root = tree.getroot()
    expectSTR = re.compile(u"([a-zA-Z]+)+")
    finded = False
    for element in root:
        if element.text:
            text = element.text
            textIgnore = text
            for ign in ignoreWords:
                textIgnore = textIgnore.replace(ign, '')
            result = expectSTR.findall(textIgnore)
            if(result):
                print u"Найдено: ",
                for word in result:
                    print word,
                print
                print u"В строке:"
                print text
                if(not finded):
                    finded = True
    if(finded):
        print path

def findXML(path):
    listOfDir = os.listdir(path)
    for element in listOfDir:
        if ".xml" in element:
            findChar(os.path.join(path, element), ignoreWords)

path = r".\DefInjected"
listOfDir = os.listdir(path)

for element in listOfDir:
    sub = os.path.join(path, element)
    if os.path.isdir(sub):
        findXML(sub)
