# hangman-bot
a Reddit bot written in Python 3.6 using PRAW and requests. It provides games of hangman to an arbitrary number of users simultaneously,
can restart while remembering active games, and stores all past games.

# Instructions
start a new game by having a mention of u/hangman_bot somewhere in your comment/pm.

reply to the bot's messages with either a single character or a whole word as your guess. Currently, you can't play anyone else's game, just yours.

the bot will reply with the updated status of the game. You'll eventually win or lose, or you can forfeit by having 'forfeit' in your reply.

if you mention the bot again while playing, you won't get a new game. You have to end the current one first. There is no branching or anything, each user gets one active game at a time.

# Improvement
- difficulty levels
- topics
- architecture and code structure
