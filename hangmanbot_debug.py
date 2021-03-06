import praw
import json
import time
import os
import random
import requests

FORFEIT = 'forfeit'
NEW_GAME = 'new game'
WIN = 'You win! Big-brained, you are.'
LOSS = 'You lose. Try again.'
MIN_LEN = 4
INIT_LIVES = 5

class Hangman:
    """represents the state of a game of Hangman"""
    def __init__(self):
        self.secret = random_word()
        self.lives = INIT_LIVES
        self.word_state = ['_'] * len(self.secret)
        self.mistakes = []
       #  self.user_id = None
    
    # classmethod: best practice for multiple constructors
    @classmethod
    def fromdict(cls, dictionary):
        """dictionary to Hangman copy/convert constructor""" 
        instance = cls()
        for key in dictionary:
            setattr(instance, key, dictionary[key])
        return instance

    def process_guess(self, guess_body):
        """requires that guess_body is single character: modifies word_state to fill in guess matches"""
        print('process_guess started')
        for i in range(0, len(self.secret)):
            print(self.secret[i])
            print(guess_body)
            if self.secret[i] == guess_body:
                self.word_state[i] = guess_body
                print(self.word_state[i])
                # self.word_state = self.word_state[:i] + guess_body + self.word_state[(i + 1):] 

    def word_correct(self, guess):
        return guess == self.secret
    
    def record_mistake(self, mistake_body):
        self.mistakes.append(mistake_body)
        self.lives -= 1

    def display_contents(self):
        """return a formatted markdown string containing a report on hangman attributes"""
        reply = ''
        reply += '\n\nlives: ' + str(self.lives) + '\n\n#'
        for char in self.word_state:
            reply += char + ' '
        reply += '\n\nmistakes: '
        reply += ', '.join(self.mistakes)
        return reply

def random_word():
    """request one random word from API. If len of word at least MIN_LEN letters, return it (str). Otherwise, request another."""
    while True:
        r = requests.get('https://random-word-api.herokuapp.com/word', {'number' : 1})
        r.raise_for_status()
        word = r.json()[0]
        if len(word) >= MIN_LEN:
            return word

def authenticate():
    r = praw.Reddit('hangman', user_agent = "hangmanbot")
    return r

def run_bot(reddit, active_games):
    # concern: maybe update_active_games_file should be done in same fn as archiving
    print('runbotstarted')
    unread_items = []
    for item in reddit.inbox.unread(limit=None):
        if bot_mentioned(item):
            start_new_game(item, active_games)
            update_active_games_file(item, active_games)
        else:
            try:
                continue_game(item, active_games)
                update_active_games_file(item, active_games)
            except Exception as e: print(e)
        unread_items.append(item)
    reddit.inbox.mark_read(unread_items)   
    time.sleep(2)

def bot_mentioned(item):
    return 'u/hangman_bot' in item.body

# reply to item with a comment containing a new Hangman game and remember it.
def start_new_game(item, active_games):
    if item.author.name not in active_games:
        new_game = Hangman()
        active_games[item.author.name] = new_game
        item.reply(new_game.display_contents())
        
# continue a game by replying to guess with the updated hangman state.
def continue_game(guess, active_games):
    game = active_games[guess.author.name]
    guess_content = guess.body.replace(' ','').replace('\n','').lower()
    if game.word_correct(guess_content):
        print('case1')
        # handle_win(guess, active_games)
        remove_and_archive_game(guess, active_games)
        guess.reply(WIN)
    elif guess_content in game.secret: # make this work for substrings > 1
        print('case2')
        game.process_guess(guess_content)
        if game.secret == ''.join(game.word_state):
            remove_and_archive_game(guess, active_games)
            guess.reply(WIN)
        else:
            guess.reply('Correct!' + game.display_contents())
    elif game.lives == 1 or FORFEIT in guess_content:
        print('case3')
        # active_games.pop(guess.author.name)
        remove_and_archive_game(guess, active_games)
        guess.reply(LOSS + '\n\nWord: ' + game.secret)
    else:
        print('case4')
        game.record_mistake(guess_content)
        guess.reply('Incorrect!' + game.display_contents())

def next_turn(guess, game):
    """continue a game by replying to single letter guess with updated game information"""

    
def handle_win(guess, active_games):
    """currently obsolete"""
    finished_game = active_games.pop(guess.author.name)
    with open('hangmanbot/archived_games.txt', 'w') as f:
        archived_games = json.load(f)
        if guess.author.name not in archived_games:
            archived_games[guess.author.name] = [finished_game.__dict__]
        else:
            archived_games[guess.author.name].append(finished_game.__dict__)
        json.dump(archived_games, f)
    guess.reply(WIN)

def remove_and_archive_game(guess, active_games):
    """remove guess author's game from active, place entry in archive file"""
    finished_game = active_games.pop(guess.author.name)
    # automate file creation as well, don't create it manually.
    if not os.path.isfile('hangmanbot/archived_games.txt'):
        with open('hangmanbot/archived_games.txt', 'w') as f:
            json.dump({guess.author.name : [finished_game.__dict__]}, f)
    else: # whoops, can't read a file if open with w, r+ is read and write
        with open('hangmanbot/archived_games.txt', 'r+') as f:
            archived_games = json.load(f)
            if guess.author.name not in archived_games:
                archived_games[guess.author.name] = [finished_game.__dict__]
            else:
                archived_games[guess.author.name].append(finished_game.__dict__)
            # seek(0), dump, truncate completely overwrites the file contents.
            f.seek(0)
            json.dump(archived_games, f)
            f.truncate()


    
# update the save file by writing a new active game or modifying an existing game.
def update_active_games_file(item, active_games): 
    copied = dict()
    for key in active_games:
        copied[key] = active_games[key].__dict__
    with open('hangmanbot/active_games.txt', 'w') as f:
        json.dump(copied, f)

# return a dict of <username, Hangman> corresponding to active games.
def get_active_games():
    if not os.path.isfile("hangmanbot/active_games.txt"):
        return dict()
    else:
        with open("hangmanbot/active_games.txt") as f:
            dict_with_dicts = json.load(f)
            print(dict_with_dicts)
            dict_with_objects = dict()
            for key in dict_with_dicts:
                dict_with_objects[key] = Hangman.fromdict(dict_with_dicts[key])
            return dict_with_objects

# main function: so this module can be imported without executing main functionality.
def main():
    reddit = authenticate()
    active_games = get_active_games()
    print(active_games)
    while True:
        run_bot(reddit, active_games)

## end definitions
## begin executions
if __name__ == '__main__':
    main()