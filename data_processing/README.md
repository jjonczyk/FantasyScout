# Data Processing

This stage is handled through two mechanisms, and the selection of the appropriate one depends on at what point in the season it is launched.

### The inter-season period

Between seasons, we have to predict how the players will perform in the upcoming games. 
To do so, a regression model is trained on historical data, and then a prediction is performed on future data.
This stage still has a lot of room for development and will be improved in the future.

### The period during a season

If the season is ongoing and several GW have passed, it can be considered that the amount of data acquired so far is reliable.
In this case, algorithms that mimic human reasoning are used to make the best choices. 
Among the attributes included are:
- looking for mismatches (strong vs weak team)
- points per game
- player's form in the last few games
- the ratio of a player's quality (performance) to his price