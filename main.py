# -*- coding: utf-8 -*-

#import json
import json
import logging
import urllib
import urllib2
import datetime
from datetime import datetime
from datetime import timedelta
from time import sleep
# import requests

import key

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext import deferred

import person
import emoij
from person import Person

import webapp2


import sentAnno
import categories
import util
import bitmaptest
import emoji

from jinja2 import Environment, FileSystemLoader

# ================================
# ================================
# ================================

BASE_URL = 'https://api.telegram.org/bot' + key.TOKEN + '/'

DASHBOARD_DIR_ENV = Environment(loader=FileSystemLoader('dashboard'), autoescape = True)
tell_completed = False

STATES = {
    0:   'Initial Screen',
    1:   'Display Current Sentence',
    30:  'Add MWE: select tokens',
    31:  'Add MWE: select category',
    40:  'Action on single MWE (modify lable or remove)',
    50:  'Modify MWE',
    60:  'Remove MWE',
    70:  'Change MWE Confidence Level',
    -1:  'Settings',
    -11: 'Settings -> highlighting mode',
    -12: 'Settings -> button desity'
}

MIN_CHARS_PER_LINE = 10
MAX_CHARS_PER_LINE = 50

CANCEL = u'\U0000274C'.encode('utf-8')
CHECK = u'\U00002705'.encode('utf-8')
PEN = u'\U0001F58B'.encode('utf-8')
UNDER_CONSTRUCTION = u'\U0001F6A7'.encode('utf-8')
NEXT = u'\U000025B6'.encode('utf-8')
PREV = u'\U000025C0'.encode('utf-8')
DOUBLE_NEXT = u'\U000023E9'.encode('utf-8')
DOUBLE_PREV = u'\U000023EA'.encode('utf-8')
JUMP_ARROW = u'\U00002935'.encode('utf-8')
WRITE = u'\U0000270D'.encode('utf-8')
MEMO = u'\U0001F4DD'.encode('utf-8')
SOS = u'\U0001F198'.encode('utf-8')
TOOLS = u'\U0001F6E0'.encode('utf-8')
GEAR = u'\U00002699'.encode('utf-8')
SLIDER = u'\U0001F39A'.encode('utf-8')
CRAYON = u'\U0001F58D'.encode('utf-8')
RULER = u'\U0001F4CF'.encode('utf-8')
EXCLAMATION = u'\U00002757'.encode('utf-8')
WRENCH = u'\U0001F527'.encode('utf-8')
PLUS = u'\U00002795'.encode('utf-8')
EMPTY_PAGE = u'\U0001F5D2'.encode('utf-8')
EMPTY_BIN = u'\U0001F5D1'.encode('utf-8')
FROWNING_FACE = u'\U0001F641'.encode('utf-8')
NO_ENTRY = u'\U0001F6AB'.encode('utf-8')
WARNING_SIGN = u'\U000026A0'.encode('utf-8')
DASH = u'\U00000023\U000020E3'.encode('utf-8')
RIGHT_ARROW = u'\U000027A1'.encode('utf-8')
LEFT_ARROW = u'\U00002B05'.encode('utf-8')
LABEL = u'\U0001F3F7'.encode('utf-8')
CIRCLE_ARROWS = u'\U0001F504'.encode('utf-8')
LONG_DASH = u'\U00000336'.encode('utf-8')
THUMB_UP = u'\U0001F44D'.encode('utf-8')
BLACK_CROSS = u'\U00002716'.encode('utf-8')
BLACK_CHECK = u'\U00002714'.encode('utf-8')
OUT_BOX = u'\U0001F4E4'.encode('utf-8')
IN_BOX = u'\U0001F4E5'.encode('utf-8')
GRINNING_FACE = u'\U0001F600'.encode('utf-8')
INFO = u'\U00002139'.encode('utf-8')
PENCIL = u'\U0000270F'.encode('utf-8')
HISTOGRAM = u'\U0001F4F6'.encode('utf-8')
NUMBERS_0_10 = [x.encode('utf-8') for x in [u'\U00000030\U000020E3', u'\U00000031\U000020E3', u'\U00000032\U000020E3',
                                            u'\U00000033\U000020E3',u'\U00000034\U000020E3',u'\U00000035\U000020E3',
                                            u'\U00000036\U000020E3',u'\U00000037\U000020E3',u'\U00000038\U000020E3',
                                            u'\U00000039\U000020E3',u'\U0001F51F']]

ANNOTATE_BUTTON = MEMO + ' ANNOTATE'
ANNOTATE_BUTTON_EN = MEMO + ' ENGLISH ' + emoji.ENGLISH_FLAG
ANNOTATE_BUTTON_IR = MEMO + ' FARSI ' + emoji.IRAN_FLAG
HELP_BUTTON = SOS + ' HELP'
ACCEPT_BUTTON = CHECK + " OK"
CANCEL_BUTTON = CANCEL + " Abort"
CHOOSE_CAT_BUTTON = LABEL + "Assign Category"
BACK_BUTTON = emoij.LEFTWARDS_BLACK_ARROW + ' ' + "BACK"
PREV_BUTTON = PREV + ' Prev'
GO_TO_BUTTON = JUMP_ARROW + ' Jump to'
NEXT_BUTTON = NEXT + ' Next'
ANN_SENT_BUTTON = WRITE + ' Annotate Sentence'
YES_BUTTON = CHECK + " YES"
NO_BUTTON = CANCEL + " NO"
NO_MWE_BUTTON = CANCEL + " NO MWEs"
SETTINGS_BUTTON = GEAR + " SETTINGS"
HIGHTLIGHTING_MODE_BUTTON = CRAYON + ' HIGHLIGHTING MODE'
BUTTONS_DENSITY_BUTTON = RULER + ' BUTTONS DENSITY'
ADD_MWE_BUTTON = PLUS + ' ADD MWE'
MOD_MWE_BUTTON = WRENCH + ' MODIFY MWE' #PENCIL?
REMOVE_MWE_BUTTON = CANCEL + ' REMOVE MWE'
REMOVE_BUTTON = CANCEL + ' REMOVE'
CHANGE_CAT_BUTTON = LABEL + ' CHANGE CAT'
CHANGE_MWE_ELEMENTS = CIRCLE_ARROWS + ' CHANGE ELEMENTS'
CHANGE_MWE_CONFIDENCE = HISTOGRAM + ' CHANGE CONFIDENCE'
CONFIRM_CHANNGES = THUMB_UP + " CONFIRM CHANGES"
SECTION_SEPARATOR_BOTTOM = LONG_DASH * 10
INFO_BUTTON = INFO + " INFO"

INSTRUCTIONS = UNDER_CONSTRUCTION + " Instructions coming up, ... " +\
               "please help us test this system and join our group at " +\
               "https://telegram.me/joinchat/B8zsMQebmdZWW4JmeaQsaw\n" +\
               "ParsemeBot v.4"

# ================================
# ================================
# ================================

def init_user(p, name, last_name, username):
    p.name = name
    p.last_name = last_name
    p.username = username
    p.enabled = True
    p.put()

def re_init_user(p, name, last_name, username):
    changed = False
    if p.name != name:
        p.name = name
        changed = True
    if p.last_name != last_name:
        changed = True
    if p.username != username:
        p.username = username
        changed = True
    if p.enabled != True:
        p.enabled = True
        changed = True
    if changed:
        p.put()

def broadcast(msg):
    qry = Person.query().order(-Person.last_mod)
    count = 0
    for p in qry:
        if (p.enabled):
            count += 1
            tell(p.chat_id, msg)
            sleep(0.100) # no more than 10 messages per second
    logging.debug('broadcasted to people ' + str(count))

def restartAllUsers(msg):
    qry = Person.query()
    count = 0
    for p in qry:
        if (p.enabled): # or p.state>-1
            #if p.username!='kercos':
            #    continue
            count +=1
            if msg:
                tell(p.chat_id, msg)
            restart(p)
            sleep(0.100) # no more than 10 messages per second
    logging.debug("Succeffully restarted users: " + str(count))
    return count

def resetAllUsers():
    qry = Person.query()
    count = 0
    for p in qry:
        count += 1
        person.initLangaugeCounters(p)
    logging.debug("Succeffully reinitialize users: " + str(count))
    return count

def getPeopleCount():
    c = Person.query().count()
    return c

def tell_masters(msg):
    for id in key.MASTER_CHAT_ID:
        tell(id, msg)

def tell(chat_id, msg, kb=None, hideKb=True, markdown=False):
    try:
        if kb:
            resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                'chat_id': chat_id,
                'text': msg, #.encode('utf-8'),
                'disable_web_page_preview': 'true',
                'parse_mode': 'Markdown' if markdown else '',
                #'reply_to_message_id': str(message_id),
                'reply_markup': json.dumps({
                    #'one_time_keyboard': True,
                    'resize_keyboard': True,
                    'keyboard': kb,  # [['Test1','Test2'],['Test3','Test8']]
                    'reply_markup': json.dumps({'hide_keyboard': True})
                }),
            })).read()
        else:
            if hideKb:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg, #.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'parse_mode': 'Markdown' if markdown else '',
                    #'reply_to_message_id': str(message_id),
                    'reply_markup': json.dumps({
                        #'one_time_keyboard': True,
                        'resize_keyboard': True,
                        #'keyboard': kb,  # [['Test1','Test2'],['Test3','Test8']]
                        'reply_markup': json.dumps({'hide_keyboard': True})
                }),
                })).read()
            else:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg, #.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'parse_mode': 'Markdown' if markdown else '',
                    #'reply_to_message_id': str(message_id),
                    'reply_markup': json.dumps({
                        #'one_time_keyboard': True,
                        'resize_keyboard': True,
                        #'keyboard': kb,  # [['Test1','Test2'],['Test3','Test8']]
                        'reply_markup': json.dumps({'hide_keyboard': False})
                }),
                })).read()
        logging.info('send response: ')
        logging.info(resp)
    except urllib2.HTTPError, err:
        if err.code == 403:
            p = Person.query(Person.chat_id==chat_id).get()
            p.enabled = False
            p.put()
            logging.info('Disabled user: ' + p.name.encode('utf-8') + ' ' + str(chat_id))

# ================================
# ================================
# ================================


class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(
                json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

# ================================
# ================================
# ================================

def restart(p, msg = None):
    reply_txt = msg + "\n" if msg else ''
    reply_txt += "Initial Screen." + '\n\n' + "Choose a language to ANNOTATE, change your SETTINGS or ask for HELP."
    tell(p.chat_id, reply_txt, kb=[[ANNOTATE_BUTTON_IR,ANNOTATE_BUTTON_EN],[SETTINGS_BUTTON, INFO_BUTTON],[HELP_BUTTON]])
    person.setState(p, 0)

def goToSetting(p):
    text_msg = "You are in the settings pane. Plase click in one of the buton to adjust the parameters."
    kb = [[HIGHTLIGHTING_MODE_BUTTON], [BUTTONS_DENSITY_BUTTON], [BACK_BUTTON]]
    tell(p.chat_id, text_msg, kb=kb)
    person.setState(p, -1)

def goToSettingsHighlightingMode(p):
    text_msg = "Your current highlighting mode is set to: " + \
               person.getHighlightedString(p, p.highlightingMode) + "\n" + "The options are: \n\n"
    options = person.MARKDOWN_OPTIONS.keys()
    for mode in options:
        markdownChar = person.MARKDOWN_OPTIONS[mode]
        text_msg += "   " + mode + ": " + markdownChar + "sample text" + markdownChar + "\n"
    text_msg += "\nSelect an highlighting mode."
    logging.debug('dealWithSettingHighlightingMode: ' + text_msg)
    kb = [options, [BACK_BUTTON]]
    tell(p.chat_id, text_msg, kb=kb, markdown=True)
    person.setState(p, -11)

def goToSettingsButtonsDensity(p):
    text_msg = "Your current button density is set to: " + person.getHighlightedString(p,str(p.maxCharsPerLine)) + \
               " characters per line. Press on " + BACK_BUTTON +\
               'if you are happy with this choice, otherwise enter a new value between ' + \
               person.getHighlightedString(p, str(MIN_CHARS_PER_LINE)) + ' and ' +\
               person.getHighlightedString(p, str(MAX_CHARS_PER_LINE)) + '.\n\n' +\
               "The buttons below will show you how the density changes according to the value.\n\n"
    sampleSentence = "This is  a sample sentence to show you how the buttons density changes according to your settings"
    sentenceButtons = util.splitTextOnSpaces(sampleSentence)
    sentenceButtonsArrangement = util.segmentArrayOnMaxChars(sentenceButtons, p.maxCharsPerLine,)
    kb = sentenceButtonsArrangement
    kb.insert(0, [BACK_BUTTON])
    tell(p.chat_id, text_msg, kb, markdown=True)
    person.setState(p, -12)

def displayCurrentSentence(p):
    text_msg = renderSentenceWithMwesList(p)

    if p.selectedMwes == None:
        firstButtonLine = [ADD_MWE_BUTTON, NO_MWE_BUTTON]
    elif p.selectedMwes:
        firstButtonLine = [ADD_MWE_BUTTON, MOD_MWE_BUTTON, REMOVE_MWE_BUTTON]
    else:
        firstButtonLine = [ADD_MWE_BUTTON]

    kb = [firstButtonLine, [PREV_BUTTON, GO_TO_BUTTON, NEXT_BUTTON], [BACK_BUTTON]]

    #logging.debug("again in displayCurrentSentence:text_msg: " + text_msg)
    #logging.debug("again in displayCurrentSentence:kb: " + str(kb))
    tell(p.chat_id, text_msg, kb=kb, markdown=True)
    p.currentMweTmp = [] # reset current mwe var
    person.setState(p, 1)

def renderSentenceWithMwesList(p, slashedNumbers = True):
    sentenceNumber = str(person.getCurrentSentenceIndex(p) + 1)
    totalSentences = sentAnno.totalSentPersonCurrentLang(p)
    sentence_flat = util.escapeMarkdown(sentAnno.getCurrentSentenceFlat(p))
    text_msg = "Current sentence (" + \
               person.getHighlightedString(p, sentenceNumber + '/' + str(totalSentences)) + \
               '):\n\n' + \
               SECTION_SEPARATOR_BOTTOM + "\n" + \
               sentence_flat + "\n" + \
               SECTION_SEPARATOR_BOTTOM + '\n\n'
    currentMwes = p.selectedMwes
    markDownChar = person.getMarkdownChar(p)
    if currentMwes == None:
        text_msg += CANCEL + " You have " + markDownChar + "NOT" + markDownChar + " annotated this sentence."
    elif currentMwes == {}:
        text_msg += WRITE + " YOUR ANNOTATION:\n" + EMPTY_BIN + " You marked this sentence with " + \
              markDownChar + "NO MWEs" + markDownChar + "."
    else:
        mweCount = len(currentMwes)
        text_msg += WRITE + " YOUR ANNOTATION: " + str(mweCount) + " MWE" + \
                    ("s:" if mweCount>1 else ":") + "\n" + renderSelectedMwes(p, slashedNumbers)
    return text_msg

def renderSentence(p, escapeMarkDown=True):
    sentenceNumber = str(person.getCurrentSentenceIndex(p) + 1)
    totalSentences = sentAnno.totalSentPersonCurrentLang(p)
    if escapeMarkDown:
        sentence_flat = util.escapeMarkdown(sentAnno.getCurrentSentenceFlat(p))
    else:
        sentence_flat = sentAnno.getCurrentSentenceFlat(p)
    text_msg = "Current sentence (" + sentenceNumber + \
               '/' + str(totalSentences) + '):\n\n' + \
               SECTION_SEPARATOR_BOTTOM + "\n" + \
               sentence_flat + "\n" + \
               SECTION_SEPARATOR_BOTTOM
    return text_msg

def renderSelectedMwes(p, slashedNumbers):
    currentMwes = p.selectedMwes
    result = ""
    index = 0
    for k in sorted(currentMwes.keys()):
        index += 1
        number = " /" + str(index) if slashedNumbers else str(index)
        result +=  DASH + number + ": " + renderMwe(p, k, True, True) + "\n"
    return result.strip()


def prepareToSelectTokens(p):
    text_msg = renderSentence(p, False)
    sentence_tokens = sentAnno.getCurrentSentenceTokens(p)
    p.selectedTokens = [False] * len(sentence_tokens)
    kb = segmentTokenButtons(p, sentence_tokens, p.selectedTokens, p.maxCharsPerLine)
    kb.append([BACK_BUTTON])
    tell(p.chat_id, text_msg, kb=kb)
    person.setState(p, 30)

def segmentTokenButtons(p, sentence_tokens, selected_tokens, maxCharsPerLine):
    #logging.debug('selected_tokens: ' + str(selected_tokens))
    check_buttons_with_numbers = []
    token_count = 1
    check_mark_space = CHECK + ' '
    for t in sentence_tokens:
        selected = check_mark_space if selected_tokens[token_count-1] else ""
        button_text = selected + t + ' [' + str(token_count) + ']'
        check_buttons_with_numbers.append(button_text)
        token_count += 1
    buttons = util.segmentArrayOnMaxChars(check_buttons_with_numbers, maxCharsPerLine, check_mark_space)
    #logging.debug("in segmenetedTokenButtons:")
    #logging.debug(" maxCharsPerLine: " + str(maxCharsPerLine))
    #logging.debug(" selected: " + str(selected))
    #lenArray = [sum([len(x.decode('utf-8')) for x in line]) for line in buttons]
    #logging.debug(" lineWidths: " + str(lenArray))
    if not sentAnno.LANGUAGE_LEFT_TO_RIGHT[p.language]:
        buttons = [x[::-1] for x in buttons]
    return buttons

def dealWithTokensSelection(p, token_index=None):
    # coming here form 30/31 (via add) or 40 (via /number)
    sentence_word_tokens, sentence_tokens = sentAnno.getCurrentSentenceWordTokensSentenceTokens(p)
    #logging.debug('token_index: ' + str(token_index))
    if token_index!=None:
        p.selectedTokens[token_index] = not p.selectedTokens[token_index]
    text_msg = renderSentenceWithMweHighlights(p, sentence_word_tokens, p.selectedTokens, person.getMarkdownChar(p))
    if sum(p.selectedTokens)<2:
        text_msg += "\n\n" + "Please select at least 2 tokens you want to include in the MWE."
    kb = segmentTokenButtons(p, sentence_tokens, p.selectedTokens, p.maxCharsPerLine)
    logging.debug('in dealWithTokensSelection state: ' + str(p.state))
    if sum(p.selectedTokens)>1:
        logging.debug('person.getSelectedTokensIndexTuple(p): ' + str(person.getSelectedTokensIndexTuple(p)))
        logging.debug('p.currentMweTmp: ' + str(p.currentMweTmp))
        if p.currentMweTmp:
            if person.getSelectedTokensIndexTuple(p) != tuple(p.currentMweTmp):
                #via /number press
                kb.append([CONFIRM_CHANNGES])
        else:
            # via + add
            kb.append([CHOOSE_CAT_BUTTON])

    kb.append([BACK_BUTTON])
    tell(p.chat_id, text_msg, kb=kb, markdown=True)
    person.setState(p, 30)

def renderSentenceWithMweHighlights(p, sentence_word_tokens, selectedTokens, markdownChar):
    result = ""
    token_index = 0
    for w in sentence_word_tokens:
        for t in w:
            if selectedTokens[token_index] and not person.containsMarkdownSymbols(t):
                # Tags must not be nested. https://core.telegram.org/bots/api#formatting-options
                result += markdownChar + t + markdownChar
            else:
                result += util.escapeMarkdown(t)
            token_index += 1
        result += ' '
    result.strip()
    logging.debug("renderedSentence: " + result)
    return result

def renderMwe(p, indexes, showCategory = False, showConfidence = False):
    result = ""
    sentence_word_tokens = sentAnno.getCurrentSentenceSplitSpaceToken(p)  # [[tok1,tok2],[tok3,tok4],...]
    token_index = 0
    started = False
    hasGap = False
    markdownChar = person.getMarkdownChar(p)
    for w in sentence_word_tokens:
        selectedWord = False
        for t in w:
            num = '(' + str(token_index + 1) + ')'
            if person.containsMarkdownSymbols(t):
                # Tags must not be nested. https://core.telegram.org/bots/api#formatting-options
                ecaped_md_num_token = util.escapeMarkdown(t + num)
            else:
                ecaped_md_num_token = markdownChar + t + markdownChar + num
            if token_index in indexes:
                if hasGap:
                    result += "... "
                    hasGap = False
                result += ecaped_md_num_token
                started = True
                selectedWord = True
            elif started:
                hasGap = True
            token_index += 1
        if selectedWord:
            result += ' '
    result.strip()
    if showCategory or showConfidence:
        if sentAnno.LANGUAGE_LEFT_TO_RIGHT[p.language]:
            ARROW = RIGHT_ARROW
        else:
            ARROW = LEFT_ARROW
        cat, conf = sentAnno.getCategoryAndConfidence(p,indexes)
        if showCategory:
            category = person.getHighlightedString(p, cat)
            result += " " + ARROW + " " + category
        if sentAnno.CONFIDENCE_ACTIVE and showConfidence:
            confidence = ' ' + HISTOGRAM + '=' + NUMBERS_0_10[conf] if sentAnno.CONFIDENCE_ACTIVE else ''
            result += confidence
    return result

def askAnnotationLabel(p):
    indexes = person.getSelectedTokensIndexTuple(p)
    logging.debug("in askAnnotationLabel. last state: " + str(p.last_state))
    changeCategory = p.state==40
    mwe_flat = renderMwe(p, indexes, changeCategory, False)
    text_msg = renderSentence(p) + "\n\n"
    text_msg += "You have selected the following MWE:\n" + mwe_flat + "\n\n"
    if changeCategory:
        text_msg += "which NEW category do you want to assign to it?"
    else:
        text_msg += "which category do you want to assign to it?"
    kb = util.segmentArrayOnMaxChars(categories.ANNOTATION_CATS, p.maxCharsPerLine)
    #kb = categories.ANNOTATION_CATS_SPLIT_ON_CHAR #sentences.ANNOTATION_CATS_3PL
    kb.append([BACK_BUTTON])
    tell(p.chat_id, text_msg, kb=kb, markdown=True)
    person.setState(p, 31)

def askConfidenceLevel(p):
    indexes = person.getSelectedTokensIndexTuple(p)
    sentAnno.getCategoryAndConfidence(p, indexes)
    mwe_flat = renderMwe(p, indexes, True, True)
    text_msg = "You have selected the following MWE:\n" + mwe_flat + "\n\n"
    text_msg += "Which NEW confidence level do you want to assign to it? Please enter a number between 1 and 10"
    kb = util.makeArray2D(NUMBERS_0_10[1:],5)
    kb.append([BACK_BUTTON])
    tell(p.chat_id, text_msg, kb, markdown=True)
    person.setState(p, 70)


def askWhichAnnotationToModify(p):
    currentMwes = p.selectedMwes
    size = len(currentMwes)
    if size==1:
        jumpToModifySingleMwe(p, 1)
        # state 40
    else:
        text_msg = renderSentenceWithMwesList(p, False)
        text_msg += "\n\n" + "Which MWE do you want to modify? " \
                           "Enter the corresponding index between 1 and " + str(size) + "."
        numberArray = [str(x+1) for x in range(0,size)]
        kb = util.distributeElementMaxSize(numberArray, 5)
        kb.append([BACK_BUTTON])
        #logging.debug("keyboard: " + str(kb) )
        tell(p.chat_id, text_msg, kb=kb, markdown=True)
        person.setState(p, 50)


def askWhichAnnotationToRemove(p):
    currentMwes = p.selectedMwes
    size = len(currentMwes)
    if size == 1:
        dealWithRemoveMwe(p, 1)
        #state 1
    else:
        text_msg = renderSentenceWithMwesList(p, False)
        text_msg += "\n\n" + "Which MWE do you want to remove? " \
                           "Enter the corresponding index between 1 and " + str(size) + "."
        numberArray = [str(x+1) for x in range(0,size)]
        kb = util.distributeElementMaxSize(numberArray, 5)
        kb.append([BACK_BUTTON])
        #logging.debug("keyboard: " + str(kb) )
        tell(p.chat_id, text_msg, kb=kb, markdown=True)
        person.setState(p, 60)

def dealWithRemoveMwe(p, mwe_number):
    currentMwes = p.selectedMwes
    if mwe_number > 0 and mwe_number <= len(currentMwes):
        remove_index = mwe_number - 1
        mwe_to_remove = sorted(currentMwes.keys())[remove_index]
        mwe_flat = renderMwe(p, mwe_to_remove, True, True)
        sentAnno.removeMwe(p, mwe_to_remove) #mirroring on person
        #person.removeMwe(p, mwe_to_remove)
        tell(p.chat_id, CHECK + " The MWE " + mwe_flat + " has been removed!", markdown=True)
        displayCurrentSentence(p)
        # state 1
    else:
        tell(p.chat_id, "Not a valid mwe index.")

def jumpToModifySingleMwe(p, mwe_number):
    if mwe_number < 0 or mwe_number > len(p.selectedMwes):
        tell(p.chat_id, EXCLAMATION + " Not a valid MWE index.")
        return
    #logging.log("in jumpToModifySingleMwe: " + str(p.selectedMwes))
    mwe_indexes = sorted(p.selectedMwes)[mwe_number-1]
    person.setSelectedTokenFromIndexList(p, mwe_indexes)
    mwe_flat = renderMwe(p, mwe_indexes, True, True)
    text_msg = renderSentence(p) + "\n\n"
    text_msg += "You have selected the following MWE:\n" + mwe_flat + \
                "\n\n" + "How do you want to modify it?"
    first_line_kb = [CHANGE_CAT_BUTTON, REMOVE_BUTTON]
    second_line_kb = [CHANGE_MWE_ELEMENTS]
    if sentAnno.CONFIDENCE_ACTIVE:
        second_line_kb.append(CHANGE_MWE_CONFIDENCE)
    kb = [first_line_kb, second_line_kb, [BACK_BUTTON]]
    tell(p.chat_id, text_msg, kb=kb, markdown=True)
    person.setState(p, 40)

def dealWithChangeMwe(p):
    currentMweTmpTuple = tuple(p.currentMweTmp)
    category, confidence = sentAnno.getCategoryAndConfidence(p, currentMweTmpTuple)
    mwe_flat_old = renderMwe(p, currentMweTmpTuple, True, False)
    new_indexes = person.getSelectedTokensIndexTuple(p)
    sentAnno.removeMwe(p, currentMweTmpTuple) #mirroring on person
    #person.removeMwe(p, currentMweTmpTuple)
    sentAnno.appendMwe(p, category) #mirroring on person
    #person.appendMwe(p, category)
    mwe_flat_new = renderMwe(p, new_indexes, True, False)
    tell(p.chat_id, CHECK + " Successfully changed MWE:\n" +
         OUT_BOX + ' ' + mwe_flat_old + "\n" +
         IN_BOX + ' ' + mwe_flat_new + "\n", markdown=True)
    displayCurrentSentence(p)

def dealWithChangeConfidenceLevel(p, newConf):
    currentMweTuple = person.getSelectedTokensIndexTuple(p)
    #currentMweTuple = tuple(p.currentMweTmp)
    oldCat, oldConf = sentAnno.getCategoryAndConfidence(p, currentMweTuple)
    sentAnno.changeConfidenceCurrentMWE(p,newConf) #mirroring on person
    oldConfEmoji = NUMBERS_0_10[oldConf]
    newConfEmoji = NUMBERS_0_10[newConf]
    tell(p.chat_id, CHECK + " Successfully changed MWE confidence from " + oldConfEmoji + " to " + newConfEmoji, markdown=True)
    displayCurrentSentence(p)

def jumpToSentence(p, index):
    person.goToSentece(p, index - 1)
    person.importSelectedMwe(p)
    displayCurrentSentence(p)

# ================================
# ================================
# ================================


class WebhookHandler(webapp2.RequestHandler):

    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        # update_id = body['update_id']
        message = body['message']
        #message_id = message.get('message_id')
        # date = message.get('date')
        if "chat" not in message:
            return
        # fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']
        if "first_name" not in chat:
            return
        text = message.get('text').encode('utf-8') if "text" in message else ""
        name = chat["first_name"].encode('utf-8')
        last_name = chat["last_name"].encode('utf-8') if "last_name" in chat else "-"
        username = chat["username"] if "username" in chat else "-"
        #location = message["location"] if "location" in message else None
        #logging.debug('location: ' + str(location))

        def reply(msg=None, kb=None, hideKb=True, markdown=False):
            tell(chat_id, msg, kb, hideKb, markdown)

        p = ndb.Key(Person, str(chat_id)).get()

        if p is None:
            # new user
            logging.info("Text: " + text)
            if text == '/help':
                reply(INSTRUCTIONS)
            elif text.startswith("/start"):
                tell_masters("New user: " + name)
                p = person.addPerson(chat_id, name, last_name, username)
                reply("Hi " + name + ", " + "welcome to the Parseme Shared Task annotation!")
                restart(p)
            else:
                reply("Something didn't work... please contact @kercos")
        else:
            # known user
            person.updateUsername(p, username)
            if text=='/state':
                if p.state in STATES:
                    reply("You are in state " + str(p.state) + ": " + STATES[p.state])
                else:
                    reply("You are in state " + str(p.state))
            elif text.startswith("/start"):
                reply("Hi " + name + ", " + "welcome back to the Parseme Shared Task annotation!")
                person.reInitializePerson(p, chat_id, name, last_name, username)
                restart(p)
            #-------------
            # SETTINGS
            #-------------
            elif p.state == -1:
                # settings
                if text == BACK_BUTTON:
                    restart(p)
                elif text == HIGHTLIGHTING_MODE_BUTTON:
                    goToSettingsHighlightingMode(p)
                    # state -11
                elif text == BUTTONS_DENSITY_BUTTON:
                    goToSettingsButtonsDensity(p)
                    # state -12
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            elif p.state == -11:
                # settings -> hightlighting mode
                if text == BACK_BUTTON:
                    goToSetting(p)
                elif text in person.MARKDOWN_OPTIONS.keys():
                    person.setHighlightingMode(p, text)
                    reply("Successfully set highlighting mode to " + person.getHighlightedString(p, text),
                          markdown=True)
                    goToSetting(p)
                    #state -1
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            elif p.state == -12:
                # settings -> buttons density
                if text == BACK_BUTTON:
                    goToSetting(p)
                elif util.RepresentsInt(text):
                    charPerLine = int(text)
                    tot_sentences = sentAnno.totalSentPersonCurrentLang(p)
                    if charPerLine >= MIN_CHARS_PER_LINE and charPerLine <= MAX_CHARS_PER_LINE:
                        person.setMaxCharsPerLine(p, charPerLine)
                        goToSettingsButtonsDensity(p)
                        # state -1
                    else:
                        reply("Sorry, not a valid index. Please enter an index between " +
                              person.getHighlightedString(p,str(MIN_CHARS_PER_LINE)) + " and " +
                              person.getHighlightedString(p,str(MAX_CHARS_PER_LINE)) + ".")
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            # -------------
            # INITIAL STATE
            # -------------
            elif p.state == 0:
                # INITIAL STATE
                if text in ['/help',HELP_BUTTON]:
                    reply(INSTRUCTIONS)
                elif text == SETTINGS_BUTTON:
                    goToSetting(p)
                    #state -1
                elif text == INFO_BUTTON:
                    textMsg = "Number of annotated sentences per language:\n"
                    for lang,flag in sentAnno.LANGUAGE_FLAGS.iteritems():
                        progress = str(person.getLanguageProgress(p,lang))
                        total = str(sentAnno.totalSentLang(lang))
                        textMsg += flag + ' ' + progress + '/' + total + '\n'
                    reply(textMsg)
                elif text == ANNOTATE_BUTTON_EN:
                    person.setLanguage(p, 'ENGLISH')
                    person.importSelectedMwe(p)
                    displayCurrentSentence(p)
                    #state 1
                elif text == ANNOTATE_BUTTON_IR:
                    person.setLanguage(p, 'FARSI')
                    person.importSelectedMwe(p)
                    displayCurrentSentence(p)
                    # state 1
                elif chat_id in key.MASTER_CHAT_ID:
                    if text == '/test':
                        logging.debug('test')
                        #description = object.getObjectsById(4866725958909952)
                        #logging.debug('description: ' + description)
                        #logging.debug('type: ' + str(type(description)))
                        #reply(description)
                        #reply("Méthode de Français")
                        #deferred.defer(tell_fede, "Hello, world!")
                    elif text == '/testMarkdown':
                        reply("aaaa*xxxx*zzzzz\naaaa_xxxx_zzzz\naaaa`xxxx`zzzz", markdown=True)
                        #reply("fdsadfa [dfsafd] dsfasdf a", markdown=True)
                        #reply("fdasfd *df\\*as* fa fsa", markdown=True)
                        #text = "*" + util.escapeMarkdown("`[8]") + "*"
                        #reply(text, markdown=True)
                        #logging.debug("reply text: " + text)
                    elif text == '/testBitMap':
                        #bitmaptest.testBitMap(100, 20)
                        bitmaptest.testBitMap(5000, 500)
                        reply('Successfully finished test (see log).')
                    elif text.startswith('/broadcast ') and len(text)>11:
                        msg = text[11:] #.encode('utf-8')
                        deferred.defer(broadcast, msg)
                    elif text=='/restartAllUsers':
                        deferred.defer(restartAllUsers, "ParsemeBot v.2 is out! " + GRINNING_FACE )
                    elif text == '/resetAllUsers':
                        c = resetAllUsers()
                        reply("Resetted users: " + str(c))
                    else:
                        reply(FROWNING_FACE + " Sorry, I can't understand...")
                    #setLanguage(d.language)
                else:
                    reply(FROWNING_FACE + "Sorry I didn't understand you ...\n" +
                          "Press the HELP button to get more info.")
            # --------------------------
            # DISPLAY CURRENT SENTENCE
            # --------------------------
            elif p.state == 1:
                # display current sentence
                if text==BACK_BUTTON:
                    restart(p)
                elif text == '/progress':
                    reply("Annotated sentence(s) for " + p.language + ': ' +
                          str(person.getLanguageProgress(p)) + '/' + str(sentAnno.totalSentPersonCurrentLang(p)))
                elif text == '/nextna':
                    index = person.getNextNonAnnSentIndex(p)
                    if index:
                        jumpToSentence(p, index+1)
                    else:
                        reply(EXCLAMATION + " No next non-annotated sentence")
                elif text == '/prevna':
                    index = person.getPrevNonAnnSentIndex(p)
                    if index:
                        jumpToSentence(p, index + 1)
                    else:
                        reply(EXCLAMATION + " No previous non-annotated sentence")
                elif text == ADD_MWE_BUTTON:
                    prepareToSelectTokens(p)
                    #state 30
                elif text == NO_MWE_BUTTON and p.selectedMwes == None:
                    reply(CHECK + " The current sentence has been marked without MWEs.")
                    sentAnno.setEmptyMwes(p) #mirroring on person
                    #person.setEmptyMwes(p)
                    person.setCurrentSentenceAnnotated(p)
                    displayCurrentSentence(p)
                    # state 1
                elif text == MOD_MWE_BUTTON and p.selectedMwes != None:
                    # reply(UNDER_CONSTRUCTION + " currently working on this.")
                    askWhichAnnotationToModify(p)
                    # state 50
                elif text == REMOVE_MWE_BUTTON and p.selectedMwes != None:
                    askWhichAnnotationToRemove(p)
                    # state 60
                elif text==NEXT_BUTTON:
                    if person.hasNextSentece(p):
                        person.goToNextSentence(p)
                        person.importSelectedMwe(p)
                        displayCurrentSentence(p)
                        #state 1
                    else:
                        displayCurrentSentence(p)
                        reply(EXCLAMATION + " You reached the last sentence")
                        # state 1
                    # state 1
                elif text==PREV_BUTTON:
                    if person.hasPreviousSentece(p):
                        person.goToPrevSentence(p)
                        person.importSelectedMwe(p)
                        displayCurrentSentence(p)
                        #state 1
                    else:
                        displayCurrentSentence(p)
                        reply(EXCLAMATION + " You reached the first sentence")
                        # state 1
                    # state 1
                elif text==GO_TO_BUTTON:
                    tot_sentences = sentAnno.totalSentPersonCurrentLang(p)
                    reply("Please insert the index of the sentence you want to jumpt to, between " +
                          person.getHighlightedString(p, str(1)) + " and " +
                          person.getHighlightedString(p, str(tot_sentences)) +
                          " (you can also enter the number without pressing the " + JUMP_ARROW + " button).",
                          markdown = True)
                elif text.startswith('/') and util.RepresentsInt(text[1:]):
                    mwe_number = int(text[1:])
                    jumpToModifySingleMwe(p, mwe_number)
                    #state 40
                elif util.RepresentsInt(text):
                    index = int(text)
                    tot_sentences = sentAnno.totalSentPersonCurrentLang(p)
                    if index > 0 and index <= tot_sentences:
                        jumpToSentence(p,index)
                        # state 1
                    else:
                        reply(EXCLAMATION + "Not a valid index. If you want to jump to a specific sentence, "
                              "please enter an index between " +
                              person.getHighlightedString(p,str(1)) + " and " +
                              person.getHighlightedString(p,str(tot_sentences)) + '.', markdown=True)
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            elif p.state == 30:
                # add MWE -> select tokens
                if text==BACK_BUTTON:
                    displayCurrentSentence(p)
                    # state 1
                elif text.endswith(']'):
                    token_number_str = text[text.rindex('[')+1:-1]
                    #logging.debug('number_str: ' + token_number_str)
                    if util.RepresentsInt(token_number_str):
                        token_number = int(token_number_str)
                        if token_number>0 and token_number<=len(p.selectedTokens):
                            dealWithTokensSelection(p, token_number - 1)
                            #state 30
                        else:
                            reply("Not a valid token.")
                    else:
                        reply("Not a valid token.")
                elif text==CHOOSE_CAT_BUTTON:
                    currentMwes = p.selectedMwes
                    if currentMwes and person.getSelectedTokensIndexTuple(p) in currentMwes:
                        reply(EXCLAMATION + ' MWE has been already inserted!')
                    else:
                        askAnnotationLabel(p)
                        # state 31
                elif text==CONFIRM_CHANNGES:
                    dealWithChangeMwe(p)
                    # state 1
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            elif p.state == 31:
                # add MWE -> select category
                if text==BACK_BUTTON:
                    if p.last_state==40:
                        displayCurrentSentence(p)
                        # state 1
                    else:
                        dealWithTokensSelection(p)
                        # state 30
                elif text in categories.ANNOTATION_CATS:
                    indexes = person.getSelectedTokensIndexTuple(p)
                    mwe_flat = renderMwe(p, indexes, False, False)
                    reply(CHECK + " The MWE " + mwe_flat + " has been marked with category " +
                          person.getHighlightedString(p,text) + '\n', markdown=True)
                    sentAnno.appendMwe(p, text) #mirroring on person
                    #person.appendMwe(p, text)
                    person.setCurrentSentenceAnnotated(p)
                    displayCurrentSentence(p)
                    # state 1
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            elif p.state == 40:
                # user has selected a single MWE via the /number option
                if text == BACK_BUTTON:
                    displayCurrentSentence(p)
                    # state 1
                elif text==CHANGE_CAT_BUTTON:
                    askAnnotationLabel(p)
                    # state 31
                elif text == REMOVE_BUTTON:
                    mwe_to_remove = person.getSelectedTokensIndexTuple(p)
                    mwe_flat = renderMwe(p, mwe_to_remove, True, False)
                    #logging.debug("after REMOVE_MWE_BUTTON: " + str(mwe_to_remove))
                    #logging.debug("mwe_to_remove: " + str(mwe_to_remove))
                    #logging.debug("current mwes: " + str(p.selectedMwes))
                    sentAnno.removeMwe(p, mwe_to_remove) #mirroring on person
                    #person.removeMwe(p, mwe_to_remove)
                    tell(p.chat_id, CHECK + " The MWE " + mwe_flat + " has been removed!", markdown=True)
                    displayCurrentSentence(p)
                    # state 1
                elif text == CHANGE_MWE_ELEMENTS:
                    p.currentMweTmp = person.getSelectedTokensIndexTuple(p)
                    dealWithTokensSelection(p)
                    # state 30
                elif text == CHANGE_MWE_CONFIDENCE:
                    askConfidenceLevel(p)
                    # state 70
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            elif p.state == 50:
                # modify MWE
                if text == BACK_BUTTON:
                    displayCurrentSentence(p)
                    # state 1
                elif util.RepresentsInt(text):
                    mwe_number = int(text)
                    jumpToModifySingleMwe(p, mwe_number)
                    # state 40
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            elif p.state == 60:
                # remove MWE
                if text == BACK_BUTTON:
                    displayCurrentSentence(p)
                    # state 1
                elif util.RepresentsInt(text):
                    mwe_number = int(text)
                    dealWithRemoveMwe(p, mwe_number)
                    # state 1
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            elif p.state == 70:
                # change confidence level MWE
                if text == BACK_BUTTON:
                    displayCurrentSentence(p)
                    # state 1
                elif util.RepresentsInt(text):
                    newConf = int(text)
                    dealWithChangeConfidenceLevel(p, newConf)
                    # state 1
                elif text in NUMBERS_0_10[1:]:
                    newConf = NUMBERS_0_10.index(text)
                    dealWithChangeConfidenceLevel(p, newConf)
                    # state 1
                else:
                    reply(FROWNING_FACE + " Sorry, I can't understand...")
            else:
                reply("There is a problem (" + str(p.state).encode('utf-8') +
                      "). Report this to @kercos" + '\n')
                restart(p)


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
#    ('/_ah/channel/connected/', DashboardConnectedHandler),
#    ('/_ah/channel/disconnected/', DashboardDisconnectedHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
