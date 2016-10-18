# -*- coding: utf-8 -*-
import re
from google.appengine.ext import ndb
import person
import logging
import main
import emoji

# ================================
CONFIDENCE_ACTIVE = True
DEFAULT_CONFIDENCE = 10
# ================================

class SentenceAnnotation(ndb.Model):
    language = ndb.StringProperty()
    sentence_id = ndb.IntegerProperty()
    chat_id = ndb.IntegerProperty()
    mwes = ndb.PickleProperty()

'''
mwes structure

    tuple: {
        'CATEGORY': mweLabel,
        ['CONFIDENCE': value, (from 0 to 10 only if CONFIDENCE_ACTIVE == False)]
    }
'''

def getId(language, sentence_id, chat_id):
    return language + "_" + str(sentence_id) + "_" +  str(chat_id)

def setEmptyMwes(p):
    currentSentenceIndex = person.getCurrentSentenceIndex(p)
    sa = getOrInsertSentenceAnnotation(p.language, currentSentenceIndex, p.chat_id)
    sa.mwes = {}
    p.selectedMwes = {}  # mirroring on person #
    sa.put()

def appendMwe(p, mweLabel, confidence=DEFAULT_CONFIDENCE):
    currentSentenceIndex = person.getCurrentSentenceIndex(p)
    sa = getOrInsertSentenceAnnotation(p.language, currentSentenceIndex, p.chat_id)
    if not sa.mwes:
        sa.mwes = {}
    indexTuple = person.getSelectedTokensIndexTuple(p)
    if CONFIDENCE_ACTIVE:
        sa.mwes[indexTuple] = {
            'CATEGORY': mweLabel,
            'CONFIDENCE': confidence
        }
    else:
        sa.mwes[indexTuple] = {
            'CATEGORY': mweLabel
        }
    p.selectedMwes = sa.mwes  # mirroring on person #
    sa.put()

def changeConfidenceCurrentMWE(p,confidence):
    currentSentenceIndex = person.getCurrentSentenceIndex(p)
    indexTuple = person.getSelectedTokensIndexTuple(p)
    sa = getOrInsertSentenceAnnotation(p.language, currentSentenceIndex, p.chat_id)
    sa.mwes[indexTuple]['CONFIDENCE'] = confidence
    p.selectedMwes = sa.mwes # mirroring on person #
    sa.put()

def removeMwe(p, indexArray):
    currentSentenceIndex = person.getCurrentSentenceIndex(p)
    sa = getOrInsertSentenceAnnotation(p.language, currentSentenceIndex, p.chat_id)
    del sa.mwes[tuple(indexArray)]
    p.selectedMwes = sa.mwes  # mirroring on person #
    sa.put()


def getMwes(p):
    currentSentenceIndex = person.getCurrentSentenceIndex(p)
    id = getId(p.language, currentSentenceIndex, p.chat_id)
    sa = SentenceAnnotation.get_by_id(id)
    if sa:
        return sa.mwes
    return None

def getCategoryAndConfidence(p, indexes):
    mweTable = p.selectedMwes[indexes]
    logging.debug('In getCategoryAndConfidence. mweTable: ' + str(mweTable))
    cat = mweTable['CATEGORY']
    conf = mweTable['CONFIDENCE'] if 'CONFIDENCE' in mweTable else DEFAULT_CONFIDENCE
    return cat, conf

def getOrInsertSentenceAnnotation(language, sentence_id, chat_id):
    id = getId(language, sentence_id, chat_id)
    sa = SentenceAnnotation.get_by_id(id)
    if sa:
        return sa
    sa = SentenceAnnotation(
        id=id,
        language=language,
        sentence_id=sentence_id,
        chat_id=chat_id,
    )
    sa.put()
    return sa

SENTENCES_EN = [line.rstrip('\n') for line in open('languages/english.txt')]
SENTENCES_IR = [line.rstrip('\n') for line in open('languages/farsi.txt')]

LANGUAGE_SENTENCES = {
    'ENGLISH': SENTENCES_EN,
    'FARSI': SENTENCES_IR,
}

LANGUAGE_FLAGS = {
    'ENGLISH': emoji.ENGLISH_FLAG,
    'FARSI': emoji.IRAN_FLAG,
}


LANGUAGE_LEFT_TO_RIGHT = {
    'ENGLISH': True,
    'FARSI': False,
}


reSplitSpace = re.compile("\s")

SENTENCE_SPLIT_SPACE_EN = [
    reSplitSpace.split(x) for x in SENTENCES_EN
]

SENTENCE_SPLIT_SPACE_IR = [
    reSplitSpace.split(x) for x in SENTENCES_IR
]

reSplitTokens = re.compile("\|")

SENTENCE_SPLIT_SPACE_TOKENS_EN = [
    [reSplitTokens.split(w) for w in s] for s in SENTENCE_SPLIT_SPACE_EN
]

SENTENCE_SPLIT_SPACE_TOKENS_IR = [
    [reSplitTokens.split(w) for w in s] for s in SENTENCE_SPLIT_SPACE_IR
]

SENTENCE_SPLIT_SPACE_TOKENS = {
    'ENGLISH': SENTENCE_SPLIT_SPACE_TOKENS_EN,
    'FARSI': SENTENCE_SPLIT_SPACE_TOKENS_IR,
}

def getLanguages():
    return LANGUAGE_SENTENCES.keys()

def totalSentPersonCurrentLang(p):
    return len(LANGUAGE_SENTENCES[p.language])

def totalSentLang(lang):
    return len(LANGUAGE_SENTENCES[lang])

def getCurrentSentenceSplitSpaceToken(p):
    currentSentenceIndex = person.getCurrentSentenceIndex(p)
    return SENTENCE_SPLIT_SPACE_TOKENS[p.language][currentSentenceIndex] #[[tok1,tok2],[tok3,tok4],...]

def getCurrentSentenceTokens(p):
    sentence_word_tokens = getCurrentSentenceSplitSpaceToken(p)  # [[tok1,tok2],[tok3,tok4],...]
    sentence_tokens = [t for w in sentence_word_tokens for t in w]
    return sentence_tokens

def getCurrentSentenceFlat(p):
    sentence_word_tokens = getCurrentSentenceSplitSpaceToken(p)  # [[tok1,tok2],[tok3,tok4],...]
    sentence_flat = ' '.join([''.join(w) for w in sentence_word_tokens])
    return sentence_flat

def getCurrentSentenceWordTokensSentenceTokens(p):
    sentence_word_tokens = getCurrentSentenceSplitSpaceToken(p)  # [[tok1,tok2],[tok3,tok4],...]
    sentence_tokens = [t for w in sentence_word_tokens for t in w]
    sentence_flat = ' '.join([''.join(w) for w in sentence_word_tokens])
    return sentence_word_tokens, sentence_tokens