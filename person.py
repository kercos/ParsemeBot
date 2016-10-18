# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
import sentAnno
import logging
from bitmap import BitMap

MARKDOWN_OPTIONS = {
    'bold':'*',
    'italic':'_',
    'fixed-width':'`',
}

def containsMarkdownSymbols(text):
    for key, markdownChar in MARKDOWN_OPTIONS.iteritems():
        if markdownChar in text:
            return True
    return False

class Person(ndb.Model):
    chat_id = ndb.IntegerProperty()
    state = ndb.IntegerProperty()
    last_mod = ndb.DateTimeProperty(auto_now=True)
    last_state = ndb.IntegerProperty()
    name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    username = ndb.StringProperty()
    language = ndb.StringProperty() #current language
    enabled = ndb.BooleanProperty(default=True)
    languageSentenceIndex = ndb.PickleProperty(default={})  # for each language current sentence index [zero based]
    languageProgress = ndb.PickleProperty(default={})  # for each langauge number of annotated sentences
    selectedTokens = ndb.BooleanProperty(repeated=True)
    highlightingMode = ndb.StringProperty(default='fixed-width')
    maxCharsPerLine = ndb.IntegerProperty(default=22)
    selectedMwes = ndb.PickleProperty()
    currentMweTmp = ndb.IntegerProperty(repeated=True)

def updateUsername(p, username, put=False):
    if (p.username!=username):
        p.username = username
    if put:
        p.put()

def addPerson(chat_id, name, last_name, username):
    p = Person(
        id = str(chat_id),
        name = name,
        chat_id = chat_id,
        last_name = last_name,
        username = username,
    )
    initLangaugeCounters(p, False)
    p.put()
    return p

def reInitializePerson(p, chat_id, name, last_name, username):
    p.populate(
        name = name,
        chat_id = chat_id,
        last_name = last_name,
        username = username,
        enabled = True
    )
    p.put()

def initLangaugeCounters(p, put=True):
    for lang in sentAnno.getLanguages():
        p.languageSentenceIndex[lang] = 0
        size = sentAnno.totalSentLang(lang)
        p.languageProgress[lang] = BitMap(size)
    if put:
        p.put()

def getCurrentSentenceIndex(p):
    return p.languageSentenceIndex[p.language]

def getLanguageProgress(p, lang=None):
    if not lang:
        lang = p.language
    return p.languageProgress[lang].count()

def setCurrentSentenceAnnotated(p, put=False):
    index = p.languageSentenceIndex[p.language]
    p.languageProgress[p.language].set(index)
    if put:
        p.put()

def getSelectedTokensIndexTuple(p):
    result = []
    for i in range(0,len(p.selectedTokens)):
        if p.selectedTokens[i]:
            result.append(i)
    return tuple(result)

def setSelectedTokenFromIndexList(p, indexes):
    size = len(p.selectedTokens)
    p.selectedTokens = [False] * size
    for i in range(0,size):
        if i in indexes:
            p.selectedTokens[i] = True

def goToSentece(p, n, put=False):
   #p.currentSentence = n
   p.languageSentenceIndex[p.language] = n
   if put:
       p.put()

def goToNextSentence(p, put=False):
    goToSentece(p, p.languageSentenceIndex[p.language]+1, put)

def goToPrevSentence(p, put=False):
    goToSentece(p, p.languageSentenceIndex[p.language]-1, put)

def hasNextSentece(p):
    #logging.debug("current: " + str(getCurrentSentenceIndex(p)))
    #logging.debug("last: " + str(sentenceAnnotation.totalSentences(p) - 1))
    return getCurrentSentenceIndex(p)<(sentAnno.totalSentPersonCurrentLang(p) - 1)

def hasPreviousSentece(p):
    return getCurrentSentenceIndex(p)>0

def getNextNonAnnSentIndex(p):
    bm = p.languageProgress[p.language]
    start = getCurrentSentenceIndex(p) + 1
    end = sentAnno.totalSentPersonCurrentLang(p)
    for index in range(start,end):
        if not bm.test(index):
            return index
    return None

def getPrevNonAnnSentIndex(p):
    bm = p.languageProgress[p.language]
    start = 0
    end = getCurrentSentenceIndex(p)
    for index in reversed(range(start,end)):
        if not bm.test(index):
            return index
    return None

def enable_user(p):
    p.enabled = True
    p.put()

def setState(p, newstate, put=True):
    p.last_state = p.state
    p.state = newstate
    if put:
        p.put()

def setLanguage(p, language, put=False):
    p.language = language
    if put:
        p.put()

def getMarkdownChar(p):
    return MARKDOWN_OPTIONS[p.highlightingMode]

def setHighlightingMode(p, mode, put=False):
    p.highlightingMode = mode
    if put:
        p.put()

def setMaxCharsPerLine(p, maxCharsPerLine, put=False):
    p.maxCharsPerLine = maxCharsPerLine
    if put:
        p.put()

def getHighlightedString(p, text):
    markdownChar = getMarkdownChar(p)
    return markdownChar + text + markdownChar

def importSelectedMwe(p, put=False):
    p.selectedMwes = sentAnno.getMwes(p)
    #logging.debug("original MWE: " + str(sentenceAnnotation.getMwes(p)))
    #logging.debug("imported MWE: " + str(p.selectedMwes))
    #logging.debug("sentence index: " + str(getCurrentSentenceIndex() + 1))
    if put:
        p.put()

'''
def appendMwe(p, mweLabel, put=False):
    if not p.selectedMwes:
        p.selectedMwes = {}
    indexTuple = getSelectedTokensIndexTuple(p)
    p.selectedMwes[indexTuple] = mweLabel
    if put:
        p.put()
'''

'''
def removeMwe(p, indexArray, put=False):
    del p.selectedMwes[indexArray]
    if put:
        p.put()
'''

'''
def setEmptyMwes(p, put=False):
    p.selectedMwes = {}
    if put:
        p.put()
'''