'''
Author: Kevin Yang, David Liu
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
    #Using the sentiment results, can also obtain the general sentiment:
    
    neg = sentiment_dict["neg"]
    neu = sentiment_dict["neu"]
    pos = sentiment_dict["pos"]
    
    if neg > neu and neg > pos:
        tweet_object.update({"overall_sentiment" : "negative_sentiment"})
    
    elif neu > pos and neu > neg:
        tweet_object.update({"overall_sentiment" : "neutral_sentiment"})
    
    elif pos > neu and pos > neg:
        tweet_object.update({"overall_sentiment" : "positive_sentiment"})
        
    elif pos == neu and pos == neg:
        tweet_object.update({"overall_sentiment" : "no_clear_sentiment"})
    
    elif pos == neu and pos != neg:
        tweet_object.update({"overall_sentiment" : "positive_neutral_sentiment"}) 
    
    elif neg == neu and neu != neg:
        tweet_object.update({"overall_sentiment" : "negative_neutral_sentiment"})    
    
    elif neg == pos and neu != pos:
        tweet_object.update({"overall_sentiment" : "positive_negative_sentiment"})    
        
    tweet_object.update({"sentiments" : sentiment_dict})
    return tweet_object
