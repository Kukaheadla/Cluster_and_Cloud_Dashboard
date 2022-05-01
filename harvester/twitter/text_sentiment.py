'''
Author: Kevin Yang
'''

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json, re, contractions

def attach_sentiment(tweet_object):
    analyzer = SentimentIntensityAnalyzer()
    sentence = tweet_object['text']
    #Remove url from string
    sentence = re.sub(r'http\S+', '', sentence).strip()
    #fix contractions
    sentence = contractions.fix(sentence, slang=True)
    #remove punctuation from string
    sentence = re.sub(r'[^\w\s]','', sentence).strip()
    #remove extra whitespace
    sentence = re.sub(r' +', ' ', sentence).strip()
    #lowercase everything
    sentence = sentence.lower()

    sentiment_dict = analyzer.polarity_scores(sentence)

    tweet_object.update({"sentiments" : sentiment_dict})
    return tweet_object
