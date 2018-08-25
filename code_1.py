import csv
import json
import sys
from collections import Counter

import pandas
import utils as utils
import vincent
import time


def tokenize(tweet):
    return utils.get_text_normalized(tweet)

def filter_terms(terms_all: list, terms_to_analyze: list):
    return list(filter(lambda term: term in terms_to_analyze, terms_all))

def read_all_important_terms(fname):
    terms = []
    if len(fname) > 0:
        with open(fname, 'r') as f:
            for line in f:
                if len(line.strip()) > 0:
                    terms.append(line.strip())
    return terms


def format_date_time(format, tweet_created_at):
    parsed_date_time = time.strptime(tweet_created_at, '%a %b %d %H:%M:%S +0000 %Y')
    formatted_date_time = time.strftime(format, parsed_date_time)
    return formatted_date_time

def analyze(fname, terms_to_analyze):
    terms_date = dict()
    count_all = Counter()
    with open(fname, 'r') as f:
        for line in f:
            # loads line as Python dictionary
            line = line.strip()
            if len(line) > 0 and line.startswith("{") and line.endswith("}"):
                tweet = json.loads(line)
                if 'text' in tweet:
                    terms_all = [term for term in tokenize(tweet)]
                    terms_all = filter_terms(terms_all, terms_to_analyze) if len(terms_to_analyze) > 0 else terms_all
                    for term in terms_all:
                        # '%Y-%m-%d %H:%M:%S',
                        formatted_date_time = format_date_time('%Y-%m-%d %H:%M', tweet['created_at'])
                        if term in terms_date:
                            terms_date[term].append(formatted_date_time)
                        else:
                            terms_date[term] = [formatted_date_time]

                # Counter update for all terms
                count_all.update(terms_all)

    return (terms_date, count_all)


def plot_term_freq(fname: str,
                   export_fname: str,
                   num_top_terms: int,
                   term_to_analyze_fname: str,
                   export_fname_for_trending_terms: str,
                   export_fname_for_non_trending_terms: str):

    terms_to_analyze = read_all_important_terms(term_to_analyze_fname)
    terms_date, count_all = analyze(fname, terms_to_analyze=terms_to_analyze)

    word_freq = count_all.most_common(num_top_terms)
    labels, freq = zip(*word_freq)
    data = {'data': freq, 'x': labels}
    bar = vincent.Bar(data, iter_idx='x')
    bar.to_json(export_fname)

    print("Term-Freq file exported at [%s]." % export_fname)

    export_terms(terms_date, count_all, labels,
                 export_fname_trending=export_fname_for_trending_terms,
                 export_fname_non_trending=export_fname_for_non_trending_terms)
    print("Terms with top trending terms are exported at [%s]" % export_fname_for_trending_terms)
    print("Terms without top trending terms are exported at [%s]" % export_fname_for_non_trending_terms)


# Plots the timeseries of top-trending terms
def plot_time_series(fname: str,
                     export_fname: str,
                     num_top_terms: int,
                     rule: str,
                     term_to_analyze_fname: str,
                     export_fname_for_trending_terms: str,
                     export_fname_for_non_trending_terms: str):

    terms_to_analyze = read_all_important_terms(term_to_analyze_fname)
    terms_date, count_all = analyze(fname, terms_to_analyze=terms_to_analyze)

    idx_list = []
    keys = []
    match_data = {}

    for term_freq_tuple in count_all.most_common(num_top_terms):
        key = term_freq_tuple[0]
        if (key != '') :
            value = terms_date[term_freq_tuple[0]]
            keys.append(key)
            ones = [1] * len(value)
            idx = pandas.DatetimeIndex(value)
            term_time_series = pandas.Series(ones, index=idx)

            # # Resampling / bucketing
            # per_minute = term_time_series.resample(rule).sum().fillna(0)
            # time_bin = term_time_series.resample(rule).sum().fillna(0)
            time_bin = term_time_series.resample(rule).sum().fillna(0)
            match_data[key] = time_bin
            idx_list.append(idx)

    all_matches = pandas.DataFrame(data=match_data,
                                   index=idx_list[0])
    # Resampling as above
    # all_matches = all_matches.resample('1Min', how='sum').fillna(0)

    # all_matches = pandas.DataFrame(data=match_data, index=idx_list[0])
    # Re-sampling for all added series
    all_matches = all_matches.resample(rule).sum().fillna(0)

    print("Terms plotted:")
    print(keys)

    time_chart = vincent.Line(all_matches[keys], width=1150, height=580)
    time_chart.axis_titles(x='Time', y='Freq')
    time_chart.legend(title='Term Timeseries')
    time_chart.to_json(export_fname)

    print("Term-Timeseries file exported at [%s]." % export_fname)

    export_terms(terms_date, count_all, keys,
                 export_fname_trending=export_fname_for_trending_terms,
                 export_fname_non_trending=export_fname_for_non_trending_terms)
    print("Terms with top trending terms are exported at [%s]" % export_fname_for_trending_terms)
    print("Terms without top trending terms are exported at [%s]" % export_fname_for_non_trending_terms)


def export_terms(terms_date: dict, terms_count: Counter, top_terms: list,
                 export_fname_trending: str, export_fname_non_trending: str):

    """
    Export the trending and non-trending terms in a csv files one for each.

    CSV Header with sample one data row is:

    +--------------+--------------------------+------------------------------------------------------------------+
    |term          |   count                  |   occurrences_at                                                 |
    |(term_string) |  (number-of-occurences)  |  (all-dates-at-which-this-term-occurred)                         |
    +------------------------------------------------------------------------------------------------------------+
    |  germany     |    2                     |  Sun Oct 22 18:21:40 +0000 2017 | Sun Oct 22 18:25:01 +0000 2017 |
    +-------------------------------------------------------------------------------------+----------------------+

    :param terms_date: dates for all terms with term as key and value as dates separated by ' | '
    :param terms_count: count for all terms with key as term and count as value
    :param top_terms: top terms that we are interested in
    :param export_fname_trending: file name to which trending terms should be exported
    :param export_fname_non_trending: file name to which non-trending terms should be exported
    :return: void
    """

    # Exporting trending terms
    with open(export_fname_trending, 'w', newline='') as csvfile:
        fieldnames = ['term', 'count', 'occurrences_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        items = []
        for key in top_terms:
            items.append({'term': key, 'count': terms_count[key], 'occurrences_at': ' | '.join(terms_date[key])})

        sorted_items = sorted(items, key=lambda k: k['count'], reverse=True)
        writer.writerows(sorted_items)

    # Exporting non-trending terms
    with open(export_fname_non_trending, 'w', newline='') as csvfile:
        fieldnames = ['term', 'count', 'occurrences_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        items = []
        for key in terms_date.keys():
            if key not in top_terms:
                items.append({'term': key, 'count': terms_count[key], 'occurrences_at': ' | '.join(terms_date[key])})

        sorted_items = sorted(items, key=lambda k: k['count'], reverse=True)
        writer.writerows(sorted_items)



if __name__ == "__main__":
    # fname = 'data/tweets.jsonl'
    fname = 'data/stream_.jsonl'
    export_fname = 'visualization/term_freq.json'
    export_non_trending_terms_fname = 'data/terms_excluding_trending_terms.csv'
    export_trending_terms_fname = 'data/trending_terms.csv'

    rule = sys.argv[2] if len(sys.argv) >= 3 else '10M'
    num_terms = int(sys.argv[3]) if len(sys.argv) >= 4 and sys.argv[3].isnumeric() else 10
    fname = sys.argv[4] if len(sys.argv) >= 5 else fname
    term_fname = sys.argv[5] if len(sys.argv) >= 6 else ""

    if len(sys.argv) >= 2 and 'timeseries' == sys.argv[1]:
        # rule is for resampling time-series into small bins
        #  possible values for S for seconds, Min for minutes
        plot_time_series(fname=fname,
                         export_fname=export_fname,
                         num_top_terms=num_terms,
                         rule=rule,
                         term_to_analyze_fname=term_fname,
                         export_fname_for_trending_terms=export_trending_terms_fname,
                         export_fname_for_non_trending_terms=export_non_trending_terms_fname)

    else:
        plot_term_freq(fname=fname,
                       export_fname=export_fname,
                       num_top_terms=num_terms,
                       term_to_analyze_fname=term_fname,
                       export_fname_for_trending_terms=export_trending_terms_fname,
                       export_fname_for_non_trending_terms=export_non_trending_terms_fname)

