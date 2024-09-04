# Welcome to the FantasyScout

This is a project dedicated to supporters of the top league in English football, especially Fantasy Premier League players.
The code allows you to search for players who should perform the best in upcoming meetings. 
Based on a quite detailed FPL datasets, an analysis is carried out, after which the program selects a ready-to-use, 15-players lineup taking into account the budget set by the creators (100M).

## Installation

1. Clone the repository to your local directory

`git clone https://github.com/jjonczyk/FantasyScout.git`

2. Enter the project directory

`cd FantasyScout`

3. Create a virtual environment

`python -m venv ./venv`

4. Activate your venv

Windows: `.\venv\Scripts\activate`
Linux: `source venv/bin/activate`

6. Install necessary libraries

`pip install -r requirements.txt`

7. Copy the data from previous seasons here: `[REPO_ROOT]/data/historical/`  
If you cannot get it from the official FPL website, you can probably find them online, e.g. there:
[vaastav's FPL](https://github.com/vaastav/Fantasy-Premier-League)

## Running the script

`python fantasy_scout.py`

As a result, an XLSX file should be created in the `[REPO]/results/` directory, marked with today's datestamp in its name.


## Pipeline

The following flowchart illustrates, in simplified form, the pipeline that is executed when the script is launched:  

![fpl-pipeline-v1](https://github.com/user-attachments/assets/afa3a931-7264-4c96-a282-f6058d970800)


## Additional info

This is a BETA version of my app. I can already see that a few aspects need to be improved, 
and I will try to develop them over the season.  
Any feedback on improvements to my project is appreciated.
