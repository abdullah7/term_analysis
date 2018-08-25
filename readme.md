# Tweet Analysis

It analyze the tweets and shows you the timeseries of the top terms.
Put tweets file in 'tweet_analyzer/data' folder.

## Install dependencies
Python3 is pre-requisite to this program.
There are some open-source python libraries used, which are listed in requirements.txt file.
YOu can install those packages by running `pip3 install -r requirements.txt`.


## Prepare Visualization Data
For visualization, first you have to analyze and create some timeseries chart-data.
Run following command to prepare that data.

`python3 code_1.py type rule top-terms file-name file-containing-terms-to-analyze`<br /><br />

`type:   The type of visualization (Options are 'timeseries', 'term-frequency')`<br />
`rule:   This is the rule for analysis which samples the timeseries data into small bins. You can use S (for seconds) T (for mins). Value 10T shows bins of 10-min and 10S will analyze with bin of 10-seconds`<br />
`top-terms:   This number of top terms to be shown in the chart. Value '10' will analyze/displays top ten terms and value 20 will do for twenty top terms.`<br />
`file-name:   The path to the file containing tweets data.`<br />
`file-containing-terms-to-analyze:   The path to the file containing terms to analyze. Each line in the file contains one term.`<br />

This program creates the json file 'term_freq.json' at 'tweet_analyzer/visualization' path.

## Exported Data
After analysis this program exports all trending terms in a file at 'data/' named 'trending_terms.csv' and
also non-trending terms as well in file named 'terms_excluding_trending_terms.csv'.

## Run Server for Visualization
Open another terminal/comand prompt in path 'tweet_analyzer/visualization'.
Run `python -m http.server 8888` which will start an http-server on port 8888.

## Open Browser and See Chart
Open browser and type `localhost:8888` and viola :)
