import praw
import pandas as pd
import datetime as dt
import string
from praw.models import MoreComments
import re
from textblob import TextBlob
from textblob.classifiers import NaiveBayesClassifier

master_posts = { 
    "title":[],
    "id":[], 
    "author" : [],
    "comms_num": [],
    "created": [],
    "body":[]
    }

master_comments = { 
    "id":[], 
    'post_id':[],
    'parent_id': [],
    "comms_num": [],
    "body":[],
    "sentiment": []
    }

def normalizeText(textstring):
    #cleaned_str=re.sub('[^a-z\s]+','',textstring,flags=re.IGNORECASE)
    cleaned_str = textstring.lower()
    cleaned_str = cleaned_str.replace('>', '')
    cleaned_str = cleaned_str.strip()
    cleaned_str = cleaned_str.replace('\n', ' ').replace('\r', ' ')
    return cleaned_str

def add(subreddit, reddit):
    print('in add')
    count = 0
    while count < 102:
        submission = subreddit.random()
        if submission.id not in master_posts["id"] and submission.num_comments > 1: 
                count +=1
                title = normalizeText(submission.title)
                master_posts["title"].append(title)
                master_posts["id"].append(submission.id)
                master_posts["author"].append(submission.author)
                master_posts["comms_num"].append(submission.num_comments)
                master_posts["created"].append(submission.created)
                body = normalizeText(submission.selftext)
                master_posts["body"].append(body)    

def processcomments(reddit, posts_df):
    #process all the individual ids and pull their comments
    posts_df.insert(3, 'deleted comms', 0)
    posts_df.insert(3, 'top level comms', 0)
    posts_df.insert(3, 'nested comms', 0)
    for ident in posts_df['id']:
        submission = reddit.submission(id=ident)
        #only pull top level comments, not replies to replies for now
        submission.comments.replace_more(limit=None)
        counter = 0
        topcounter = 0
        for comment in submission.comments.list():        
            #need to make sure its not picking up comments from OP
            counter +=1
            if 't3_' in comment.parent_id:
                topcounter +=1
            if comment.is_submitter == False and comment.body != '[removed]' and comment.body != '[deleted]':
                master_comments['id'].append(comment.id)
                master_comments['post_id'].append(ident)
                master_comments['parent_id'].append(comment.parent_id)
                master_comments['comms_num'].append(submission.num_comments)
                master_comments['body'].append(normalizeText(comment.body))
                master_comments['sentiment'].append('blank')
        posts_df.at[ident, 'deleted comms'] = submission.num_comments-counter
        posts_df.at[ident, 'top level comms'] = topcounter
        posts_df.at[ident, 'nested comms'] = counter-topcounter


def main():
    reddit = praw.Reddit(client_id='glYFKzXUunPN0w',
                     client_secret='YYVttwTqQePKNqE5RKu3kxX6mNE',
                     user_agent='APP_NAME')
    subreddit = reddit.subreddit('cscareerquestions')
    add(subreddit, reddit)
    #this was pulling posts and creating post data grame
    master_posts_df = pd.DataFrame(master_posts)
    master_posts_df.to_csv('controlposts.csv', index=False)

    processcomments(reddit, master_posts_df)
    print(len(master_comments['id']))
    print(len(master_comments['post_id']))
    print(len(master_comments['parent_id']))
    print(len(master_comments['comms_num']))
    print(len(master_comments['body']))
    print(len(master_comments['sentiment']))


    master_comments_df = pd.DataFrame(master_comments)
    
    master_comments_df.to_csv('controlcomms.csv', index=False)


if __name__ == "__main__":
    main()
