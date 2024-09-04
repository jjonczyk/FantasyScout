# Welcome to the FantasyScout

This is a project dedicated to supporters of the top league in English football, especially Fantasy Premier League players.
The code allows you to search for players who should perform the best in upcoming meetings. 
Based on a quite detailed FPL datasets, an analysis is carried out, after which the program selects a ready-to-use, 15-players lineup taking into account the budget set by the creators (100M).

## Installation

1. Clone the repository to your local directory

`git clone [link-to-repository]`

2. Create a virtual environment

`python -m venv ./venv`

3. Install necessary libraries

`pip install -r requirements.txt`

4. Copy the data from previous seasons here: `[REPO_ROOT]/data/historical/`  
If you cannot get it from the official FPL website, you can probably do so online e.g. from there:
[vaastav's FPL](https://github.com/vaastav/Fantasy-Premier-League)

## Running the script

`python fantasy_scout.py`

As a result, an XLSX file should be created in the `[REPO]/results/` directory, marked with today's datestamp in its name.

## Additional info

This is a BETA version of my app. I can already see that a few aspects need to be improved, 
and I will try to develop them over the season.  
Any feedback on improvements to my project is appreciated.