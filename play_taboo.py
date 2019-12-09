from story.story_manager_taboo import *
from generator.gpt2.gpt2_generator import *
from story.utils import *
import story.taboo_utils as taboo_utils
from termios import tcflush, TCIFLUSH
import time, sys, os
import random
import sty

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


taboo_score_start = 15
taboo_success_score_added = 10
taboo_word_used_score_penalty = 5
target_word_used_score_penalty = 10
score_penalty_per_turn = 1
chance_for_danger_when_score_below_zero = .2
taboo_victory_threshold = 100

def console_print(text,width=75,text_style='default'):
  taboo_utils.console_print(text,width,text_style)
  return

def select_game():
    with open(YAML_FILE, 'r') as stream:
        data = yaml.safe_load(stream)

    console_print("Pick a setting.", text_style='system')
    settings = data["settings"].keys()
    for i, setting in enumerate(settings):
        print_str = str(i) + ") " + setting
        if setting == "fantasy":
            print_str += " (recommended)"
        console_print(print_str, text_style='system')

    console_print(str(len(settings)) + ") custom", text_style='system')
    choice = get_num_options(len(settings)+1)

    if choice == len(settings):

        context = ""
        console_print("\nEnter a prompt that describes who you are and the first couple sentences of where you start "
                      "out ex:\n 'You are a knight in the kingdom of Larion. You are hunting the evil dragon who has been " +
                      "terrorizing the kingdom. You enter the forest searching for the dragon and see' ", text_style='system')
        prompt = input("Starting Prompt: ")
        return context, prompt

    setting_key = list(settings)[choice]

    console_print("\nPick a character", text_style='system')
    characters = data["settings"][setting_key]["characters"]
    for i, character in enumerate(characters):
        console_print(str(i) + ") " + character, text_style='system')
    character_key = list(characters)[get_num_options(len(characters))]

    name = input("\nWhat is your name? ")
    setting_description = data["settings"][setting_key]["description"]
    character = data["settings"][setting_key]["characters"][character_key]

    context = "You are " + name + ", a " + character_key + " " + setting_description + \
              "You have a " + character["item1"] + " and a " + character["item2"] + ". "
    prompt_num = np.random.randint(0, len(character["prompts"]))
    prompt = character["prompts"][prompt_num]

    return context, prompt

def instructions():
    text = '\n\n Traditional AI Dungeon instructions still apply:'
    text += '\n'
    text += '\n Enter actions starting with a verb ex. "go to the tavern" or "attack the orc."'
    text += '\n To speak enter \'say "(thing you want to say)"\' or just "(thing you want to say)" '
    text += '\n\nThe following commands can be entered for any action: '
    text += '\n  "revert"   Reverts the last action allowing you to pick a different action.'
    text += '\n  "quit"     Quits the game and saves'
    text += '\n  "restart"  Starts a new game and saves your current one'
    text += '\n  "save"     Makes a new save of your game and gives you the save ID'
    text += '\n  "load"     Asks for a save ID and loads the game if the ID is valid'
    text += '\n  "print"    Prints a transcript of your adventure (without extra newline formatting)'
    text += '\n  "help"     Prints these instructions again'
    return text

def taboo_instructions():
    text = "\nAI Dungeon 2: \"Taboo\" Instructions:"

    text += '\n\n  Taboo Edition is a mod of AI Dungeon 2.'
    text += '\n'
    text += '\n  Your goal is to get the AI Dungeon Master to say the TARGET word.'
    text += '\n  Only exact matches count. Edit: Now more flexible with matches...'
    text += '\n  You will gain ' + str(taboo_success_score_added) + ' points when the DM uses your word.'
    text += '\n  You will lose ' + str(score_penalty_per_turn) + ' point every turn.'
    text += '\n  Using TABOO words will cost you ' + str(taboo_word_used_score_penalty) +  ' points. They can be a viable strategy.'
    text += '\n  Every turn with your score below 0 has a ' + str(chance_for_danger_when_score_below_zero * 100) + '% chance of extra danger.'
    text += '\n  BEWARE: Using any form of a TABOO word is TABOO!'
    text += '\n  If you\'d like to skip your target word you can use the pass command:'
    text += '\n\n  "pass"     Skip this Taboo card, lose ' + str(score_penalty_per_turn) + ' point'
    text += '\n  (you will have to pass a lot in my experience!)'
    return text

def play_aidungeon_2():

    console_print("AI Dungeon 2: TABOO Special Edition will (NOT) save and use your actions and game to continually improve AI Dungeon. "
                  + "This feature is disabled for Taboo Hack Edition because as it would skew the story quality results.", text_style='system')

    console_print("TABOO related text will be in RED", text_style='taboo')
    #Disable uploading for Taboo
    upload_story = False
    

    console_print("\nInitializing AI Dungeon! (This might take a few minutes)\n", text_style='system')
    generator = GPT2Generator()
    console_print("Shuffling Taboo Cards. Are you ready to TABOO?", text_style='taboo')
    story_manager = UnconstrainedStoryManager(generator)
    
    print("\n")

    with open('opening.txt', 'r') as file:
        starter = file.read()
    print(starter)

    taboo_utils.taboo_score = taboo_score_start

    while True:
        if story_manager.story != None:
            del story_manager.story

        print("\n\n")
        context, prompt = select_game()
        console_print(taboo_instructions(), text_style='taboo')
        console_print(instructions(), text_style='system')
        console_print("\nGenerating story...", text_style='system')

        taboo_utils.get_random_taboo_card()


        story_manager.start_new_story(prompt, context=context, upload_story=upload_story)

        print("\n")
        console_print(str(story_manager.story), text_style='ai')
        console_print(taboo_utils.get_taboo_status(), text_style='taboo')
        while True:
            tcflush(sys.stdin, TCIFLUSH)
            action = input("> ")

            if action == "restart":
                rating = input("Please rate the story quality from 1-10: ")
                rating_float = float(rating)
                story_manager.story.rating = rating_float
                taboo_utils.taboo_score = taboo_score_start
                break

            elif action == "quit":
                rating = input("Please rate the story quality from 1-10: ")
                rating_float = float(rating)
                story_manager.story.rating = rating_float
                exit()

            elif action == "nosaving":
                upload_story = False
                story_manager.story.upload_story = False
                console_print("Saving turned off.", text_style='system')

            elif action == "help":
                console_print(instructions(), text_style='system')

            elif action == "save":
                if upload_story:
                    id = story_manager.story.save_to_storage()
                    console_print("Game saved.", text_style='system')
                    console_print("To load the game, type 'load' and enter the following ID: " + id, text_style='system')
                else:
                    console_print("Saving has been turned off. Cannot save.", text_style='system')

            elif action =="load":
                load_ID = input("What is the ID of the saved game?")
                result = story_manager.story.load_from_storage(load_ID)
                console_print("\nLoading Game...\n", text_style='system')
                console_print(result, text_style='ai')

            elif len(action.split(" ")) == 2 and action.split(" ")[0] == "load":
                load_ID = action.split(" ")[1]
                result = story_manager.story.load_from_storage(load_ID)
                console_print("\nLoading Game...\n",  text_style='system')
                console_print(result, text_style='ai')

            elif action == "print":
                console_print("\nPRINTING\n",  text_style='system')
                console_print(str(story_manager.story))

            elif action == "pass":
                console_print("PASSING",  text_style='taboo')
                taboo_utils.taboo_score = taboo_utils.taboo_score - 1
                taboo_utils.get_random_taboo_card()
                console_print(taboo_utils.get_taboo_status(), text_style='taboo')
                continue

            elif action == "revert":

                if len(story_manager.story.actions) is 0:
                    console_print("You can't go back any farther. ",  text_style='system')
                    continue

                story_manager.story.actions = story_manager.story.actions[:-1]
                story_manager.story.results = story_manager.story.results[:-1]
                console_print("Last action reverted. ",  text_style='system')
                if len(story_manager.story.results) > 0:
                    console_print(story_manager.story.results[-1], text_style='ai')
                else:
                    console_print(story_manager.story.story_start, text_style='ai')
                continue

            else:
                original_action = action

                extra_danger = ''
                if action == "":
                    action = ""
                    result = story_manager.act(action)
                    console_print(result, text_style='ai')

                elif taboo_utils.player_taboo_used_target_word_failure(original_action):
                      console_print("TABOO TARGET WORD USED. -10 POINTS. DANGER INCREASING.",  text_style='taboo')
                      extra_danger = taboo_utils.get_danger_text()
                      taboo_utils.taboo_score = taboo_utils.taboo_score - target_word_used_score_penalty + 1;
                      taboo_utils.get_random_taboo_card()

                elif taboo_utils.player_taboo_failure(original_action):
                      console_print("TABOO WORD USED. -5 POINTS.",  text_style='taboo')
                      taboo_utils.taboo_score = taboo_utils.taboo_score - taboo_word_used_score_penalty + 1;
                      #taboo_utils.get_random_taboo_card() #let them keep going, using taboo word is a risk

                elif action[0] == '"':
                    action = "You say " + action

                else:
                    action = action.strip()
                    action = action[0].lower() + action[1:]

                    if "You" not in action[:6] and "I" not in action[:6]:
                        action = "You " + action

                    if action[-1] not in [".", "?", "!"]:
                        action = action + "."

                    action = first_to_second_person(action)

                    action = "\n> " + action + "\n"

                if taboo_utils.taboo_score < 0:
                    if random.random() <= chance_for_danger_when_score_below_zero:
                        console_print("!!!", text_style='taboo')
                        extra_danger = taboo_utils.get_danger_text()

                result = "\n" + story_manager.act(action, extra_danger)

                if len(story_manager.story.results) >= 2:
                    similarity = get_similarity(story_manager.story.results[-1], story_manager.story.results[-2])
                    if similarity > 0.9:
                        story_manager.story.actions = story_manager.story.actions[:-1]
                        story_manager.story.results = story_manager.story.results[:-1]
                        console_print("Woops that action caused the model to start looping. Try a different action to prevent that.",  text_style='system')
                        continue

                if taboo_utils.taboo_score >= taboo_victory_threshold:
                    console_print(result + "\n CONGRATS YOU HAVE SURPASSEd THE TABOO ARBITRARY VICTORY THRESHOLD. CONSIDER THIS A WIN.", text_style='taboo')
                    break

                if player_won(result):
                    console_print(result + "\n CONGRATS YOU WIN", text_style='system')
                    break
                    
                if player_died(result):
                    console_print(result, text_style='ai')
                    console_print("YOU DIED. GAME OVER", text_style='system')
                    console_print("\nOptions:", text_style='system' )
                    console_print('0) Start a new game', text_style='system')
                    console_print('1) "I\'m not dead yet!" (If you didn\'t actually die) ', text_style='system')
                    console_print('Which do you choose? ', text_style='system')
                    choice = get_num_options(2)
                    if choice == 0:
                        break
                    else:
                        console_print("Sorry about that...where were we?",  text_style='system')
                        console_print(result, text_style='ai')
                else:
                    console_print(result, text_style='ai')

                if taboo_utils.player_taboo_success(result):
                    console_print("\n TABOO Score! +10 points to you.", text_style='taboo')
                    taboo_utils.taboo_score = taboo_utils.taboo_score + taboo_success_score_added
                    taboo_utils.get_random_taboo_card()
                else: 
                    taboo_utils.taboo_score = taboo_utils.taboo_score - score_penalty_per_turn

                

                console_print(taboo_utils.get_taboo_status(), text_style='taboo')
if __name__ == '__main__':
    play_aidungeon_2()
