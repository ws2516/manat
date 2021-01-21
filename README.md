# Manat Methods
A Collaborative Effort To Find Value In Sports Betting

You are here, you have made it, you are at what will become the greatest sports betting repository of our generation, or not who knows.

[The Mark 1 Model can be found here](https://manat-methods.com/sportsbettingalgorithm.html), never bust, but who knows where it will go.

There is only one real rule:
DO NOT OVERWRITE WHEN YOU PUSH, make a folder of your materials and push to that, feel free to pull others but DO NOT WRITE OVER. We will be approving git push requests so if we see such actions we will deny the push and ask what the issue is.

This repo is by no means a final product, let it be a toolbox, sandbox, whatever it is the kids call it these days, remember, you are not competing against anyone here, we can all work together to beat the book, and I have no doubt we can. Now in the coming days we will be talking about how to incorporate models here to be shared with the Manat ecosystem so we can all track and let people lose money while they fade.

From all of us here at Manat, we hope this space flourishes, invite your friend, invite everyone, experienced coder or novice, but lets make something special.

Yours truly, 
u/BrilliantScarcity354

QUICK GIT REFRESHERS:

git clone https://github.com/ws2516/manat.git -- Use this to download the git repo (only need this for initial setup). Make sure you are in the desired directory, and it will create a folder named "sportsbook" with the repo.

git pull -- run this command before editing files always. Since for now we will be working together in the main branch, this will make sure you get the latest changes updated locally (will download all changes to the repo since last edit).

git status -- run this to check check which files you have edited and not committed / staged for commit. Make sure all edited files are staged and committed before pushing.

git add [filename] -- Stages edited file or new file for commit. To change file in repo for everyone else to see must first be staged, then commited, then pushed.

git add --all -- Stages all edited / new files for commit (a good shortcut)

git commit -m "[some message here]" -- This is the unit of change (if there is a problem we can roll it back to the previous commit). Type a message to indicate what changes have been made. Even between pushes you can commit multiple times.

git push -- uploads all commits (changes) to the repo on github for all to see

some file running tips

"interpretor.py" is meant to be run at the completion of the sports day (00:00 when all games that have active bets are completed), this will ask for "here to look", that is a recap of the day, say "no" at first, then input the results of the day (array of 1s and 0s) corresponding to the bets in "masterDaily.csv", this file wil add them all and update the file. If you wish to recap the day, run the file again and answer "yes" to "are you here to look" -- this is by no means perfect so do understand you will have to debug

"processor.py" is meant to be run once a day after interpretor, this yields the relevant bets and kelly weights of all bets for the coming day

ACKNOWLEDGMENTS: We would like to acknowledge the work created by 538 which we incorporate into many of our systems and has been an incredible resource, we wish to give credit where credit is due and hope to do more to bring people into the world of probabilistic sports outcomes and informed betting.

Feel free to ping us on Reddit or on the following email: BrilliantScarcity354@gmail.com
