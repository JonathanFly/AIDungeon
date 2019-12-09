
import re
import yaml
from difflib import SequenceMatcher
import random
from sty import fg, bg, ef, rs, RgbFg

import spacy

import sys
import os
sys.path.append("./content/AIDungeon/word_forms/")
from word_forms.word_forms import get_word_forms

nlp = spacy.load('en_core_web_sm')

taboo_cards = {}
taboo_score = 15
target_word = ''
taboo_words = []
taboo_all_variants = []
target_word_all_variants = []



with open (r'/content/AIDungeon/story/taboo_cards.yaml') as file:
  taboo_cards = yaml.load(file, Loader=yaml.SafeLoader)


fg.set_style('ai', RgbFg(64, 200, 30))
fg.set_style('player', RgbFg(234, 234, 109))
fg.set_style('taboo', RgbFg(255, 15, 15))
#fg.set_style('system', RgbFg(122, 228, 102))
fg.set_style('system', RgbFg(71, 218, 46)) #have to change all the inputs to show color here


def get_danger_text():
  
  #Not currently injecting this into the story context.
  danger_options = [
    "This is a dangerous situation.", "Your life may be at risk here.", "Caution is warranted.", "You may be playing with fire",
    "Danger Abounds.", "Many have died like this.", "You sense your life may be short.", "Something is very wrong.", "Trouble ahead.",
    "Tensions are high.", "Survival is in question.", "There is danger here.","You have a feeling something bad may happen.",
    "Danger! There is a perturbed giraffe nearby."
  ]

  return "\n" + danger_options[random.randint(0,len(danger_options) - 1)]



def player_died(text):

    text = text.lower()
    dead_phrases = ["you die", "You die", "you died", "you are dead", "You died", "You are dead", "You're dead",
                    "you're dead", "you have died", "You have died", "you bleed out"]

    for phrase in dead_phrases:
        if phrase.lower() in text:
            return True
    return False

def player_won(text):

    text = text.lower()

    won_phrases = ["live happily ever after", "you live forever"]
    for phrase in won_phrases:
        if phrase.lower() in text:
            return True
    return False

def console_print(text, width=75, text_style='default'):
    last_newline = 0
    i = 0
    while i < len(text):
        if text[i] == "\n":
            last_newline = 0
        elif last_newline > width and text[i] == " ":
            text = text[:i] + "\n" + text[i:]
            last_newline = 0
        else:
            last_newline += 1
        i += 1

    if text_style == 'ai':
       text = fg.ai + text + rs.all
    elif text_style == 'player':
      text = ef.bold + fg.player + text + rs.all
    elif text_style == 'taboo':
      text = ef.bold + fg.taboo + text + rs.all
    elif text_style == 'system':
      text = fg.system + text + rs.all
    
    print(text)

    return

def get_random_taboo_card():
    global target_word
    global taboo_card
    global taboo_words
    global taboo_all_variants
    global target_word_all_variants

    taboo_card = taboo_cards[random.randint(0,len(taboo_cards) - 1)]
    target_word = list(taboo_card.keys())[0]
    taboo_words = taboo_card.get(target_word)

    
    taboo_all_variants = []
    for tw in taboo_words:
        #spacy lemmas don't give alternative word forms? too easy to cheat, let's go further
        all_forms = get_word_forms(tw.lower())
        all_forms_list = list(set().union(*all_forms.values()))
        if len(all_forms_list) > 0:
            taboo_all_variants = taboo_all_variants + all_forms_list
        else:
            taboo_all_variants = taboo_all_variants + [tw.lower()]

    target_word_forms = get_word_forms(target_word.lower())
    target_word_all_variants = list(set().union(*target_word_forms.values()))

    if not target_word_all_variants:
        target_word_all_variants = [target_word.lower()] #sometimes the library punts

    return

def player_taboo_success(text):
    
    target_word_forms = target_word_all_variants
    #target_word_forms = [target_word] #exact matches only, very hard
    #Real TABOO rules specify the word has to be exact but this might be too hard.

    text = text.lower()
    
    if target_word.lower() in text:
        return True
    
    game_generated_tokens = nlp(text)
    #check all variants
    for target_variant in target_word_forms:
      for game_token in game_generated_tokens:
        if target_variant.lower() == game_token.text.lower():
            console_print('Secret Word Detected: ' + game_token.text, text_style='taboo')
            return True
    return False

def player_taboo_failure(text):
    #print('failure check text is: ' + text)
    player_input_tokens = nlp(text.lower())

    for taboo_check_work in taboo_all_variants:
        for player_input_token in player_input_tokens:
          #print('comparing: ' + taboo_check_work + ' - ' + player_input_token.lemma_)
          if taboo_check_work == player_input_token.lemma_:
            console_print('Taboo Word Used: ' + player_input_token.lemma_, text_style='taboo')
            return True
    return False

def player_taboo_used_target_word_failure(text):
    #print('failure check text is: ' + text)
    player_input_tokens = nlp(text.lower())

    for taboo_check_word in target_word_all_variants:
        for player_input_token in player_input_tokens:
          #print('comparing: ' + taboo_check_work + ' - ' + player_input_token.lemma_)
          if taboo_check_word == player_input_token.lemma_:
            console_print('Target Word Used: ' + player_input_token.lemma_, text_style='taboo')
            return True
    return False


def get_taboo_status():
    text = "\nTARGET: " + target_word + ' | TABOO: ' + ','.join(taboo_words) +  ' | Score: ' + str(taboo_score)
    #text += "\n" + str(taboo_all_variants) #debug
    #text += "\n" + str(target_word_all_variants) #debug
    return text