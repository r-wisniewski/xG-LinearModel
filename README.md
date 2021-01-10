# Purpose
Working off of my initial python/SQL based AHL xG model, I decided implement it as a linear model using tensorflow. 

# Usage

1. The first step is scraping data from the AHL website.
The ahl_scraper.py script gets all x,y shot & goal locations at a certain strength from the AHL website and exports that to a csv file. This script should be run once to generate training data and a second time to generate the testing data.
```
command: Usage: python ahl_scraper.py [start game ID] [last game ID] [output csv name]
```
Where the game ID can be found by going to theahl.com website, finding the most recent completed game and extracting the game ID from the URL
```
for example, the game ID for this URL: https://theahl.com/stats/game-center/1019145 is 1019145
```

# Future Work

Scraping richer data (data with more features) would allow one to predict xG for a (x,y,strength) combination but also add in additional features to predict on.

# Contact

Robin Wisniewski – [LinkedIn](https://www.linkedin.com/in/robin-wisniewski/) –  [wisniewski.ro@gmail.com](mailto:wisniewski.ro@gmail.com)
