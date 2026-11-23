import random

while True:
    user = input("pick 'rock', 'paper', or 'scissor': ").lower()
        
    game_options = ['rock', 'paper', 'scissor']
    computer = random.choice(game_options)

    if user == 'rock' or user == 'paper' or user == 'scissor':
        # Game conditionals
        if user == 'rock' and computer == 'scissor':
                print(f"The user picked {user} and computer picked {computer}")
                print('You win!')
        elif user == 'scissor' and computer == 'paper':
                print(f"The user picked {user} and computer picked {computer}")
                print('You win!')
        elif user == 'paper' and computer == 'rock':
                print(f"The user picked {user} and computer picked {computer}")
                print('You win!')
        elif user == computer:
                print(f"The user picked {user} and computer picked {computer}")
                print("It's a draw!")
        else:
                print(f"The user picked {user} and computer picked {computer}")
                print('You lose!')
    else:
        if user == 'end':
            exit(0)
        else:
            print('Wrong input')
            print(user)
        
