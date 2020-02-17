import yaml
import praw
import pandas as pd
import datetime as dt
import string
from praw.models import MoreComments
import re
from textblob import TextBlob


master_posts = { 
    "title":[],
    "id":[], 
    'topic': [],
    "author" : [],
    "comms_num": [],
    "created": [],
    "body":[]
    }
master_comments = { 
    "id":[], 
    'parent_id': [],
    "comms_num": [],
    "body":[],
    "sentiment": []
    }


with open("secret.yaml") as secretFile:
    secretDict = yaml.load(secretFile, Loader=yaml.BaseLoader)
    # Facebook page access token
    PERSONAL_USE_SCRIPT = secretDict["PERSONAL_USE_SCRIPT"]
    # Verification token for Facebook chatbot
    SECRET_KEY = secretDict["SECRET_KEY"]
    APP_NAME = secretDict["APP_NAME"]
    

def normalizeText(textstring):
    #cleaned_str=re.sub('[^a-z\s]+','',textstring,flags=re.IGNORECASE)
    cleaned_str = textstring.lower()
    cleaned_str = cleaned_str.replace('>', '')
    cleaned_str = cleaned_str.strip()
    cleaned_str = cleaned_str.replace('\n', ' ').replace('\r', ' ')
    return cleaned_str


   
def searchAdd(queries, subreddit):
    top_subreddit = subreddit.search(queries, time_filter='all')
    
    for submission in top_subreddit:
        if submission.id not in master_posts["id"] and submission.created >= 1420070400 and submission.created <=1580333940:
            title = normalizeText(submission.title)
            master_posts["title"].append(title)
            master_posts["id"].append(submission.id)
            master_posts['topic'].append('blank')
            master_posts["author"].append(submission.author)
            master_posts["comms_num"].append(submission.num_comments)
            master_posts["created"].append(submission.created)
            body = normalizeText(submission.selftext)
            master_posts["body"].append(body)


def processcomments(reddit, posts_df):
    #process all the individual ids and pull their comments
    for ident in posts_df['id']:
        submission = reddit.submission(id=ident)
        #only pull top level comments, not replies to replies for now
        submission.comments.replace_more(limit=None)
        counter = 0
        for comment in submission.comments.list():        
            #need to make sure its not picking up comments from OP
            counter +=1
            if comment.is_submitter == False and comment.body != '[removed]' and comment.body != '[deleted]':
                master_comments['parent_id'].append(comment.parent_id)
                master_comments['id'].append(comment.id)
                master_comments['comms_num'].append(submission.num_comments)
                master_comments['body'].append(normalizeText(comment.body))
                master_comments['sentiment'].append('blank')




def searches(subreddit):
    searchAdd('pregnancy', subreddit)
    searchAdd('miscarriage', subreddit)
    searchAdd('abortion', subreddit)
    searchAdd('women', subreddit)
    searchAdd('woman', subreddit)
    searchAdd('female', subreddit)
    searchAdd('feminine', subreddit)
    searchAdd('transgender', subreddit)
    searchAdd('childcare', subreddit) #need to make sure woman's issue
    searchAdd('IVF', subreddit)
    searchAdd('fertility', subreddit)
    searchAdd('equal pay', subreddit)
    searchAdd('gender bias', subreddit)
    searchAdd('female role model', subreddit)
    searchAdd('sexual harassment', subreddit)
    searchAdd('workplace harassment', subreddit)
    searchAdd('genderqueer', subreddit)
    searchAdd('gender-queer', subreddit)
    searchAdd('gender-fluid', subreddit)
    searchAdd('non-binary', subreddit)
    searchAdd('nonbinary', subreddit)
    searchAdd('gender fluid', subreddit)
    searchAdd('gender queer', subreddit)

def evaluation(df):
    correct = 0
    incorrect = 0
    for index in df.index:
        if df.at[index, 'new sent'] == df.at[index, 'sentiment']:
            correct += 1
        else:
            incorrect += 1
    print('the number of correctly evaluated posts is {}'.format(correct))
    print('the number of incorrect posts is {}'.format(incorrect))
    print('out of {}, we correctly classified {}'.format(len(df.index), correct/(len(df.index))))

def sentiment(df):
    df.insert(len(df.columns)-1, 'new sent', 'blank')
    for index in df.index:
        blob = TextBlob(df.at[index, 'body'])
        pol = blob.sentiment.polarity
        if pol > 0:
            df.at[index, 'new sent'] = 'positive'
        else:
            df.at[index, 'new sent'] = 'negative' 
    df.to_csv('sentimentized.csv', index=False)        
    evaluation(df)


def main():
    reddit = praw.Reddit(client_id='glYFKzXUunPN0w',
                     client_secret='YYVttwTqQePKNqE5RKu3kxX6mNE',
                     user_agent='APP_NAME')
    subreddit = reddit.subreddit('cscareerquestions')

    #does my training data need to include some comments from each category? how do I categorize?
    
    #searches(subreddit)

    #this was pulling posts and creating post data grame

    #master_posts_df = pd.DataFrame(master_posts)
    #master_posts_df.to_csv('fullposts.csv', index=False)

    #how to deal w race and queer issues

    #getting posts from already created CSV files
    master_posts_df = pd.read_csv('capPostSent.csv')
    master_posts_df.sort_values(by='id', inplace= True)

    #when I added sentiment
    #master_posts_df.insert(4, 'sentiment', 'blank')
    #master_posts_df.to_csv('capPostSent.csv', index=False)

    print('master posts')
    print(master_posts_df)

    #pulling comments from the posts CSV, only needs to be done once
    #posts_train = master_posts_df.iloc[:19, :]
    #processcomments(reddit, posts_train)
    #master_comments_df = pd.DataFrame(master_comments)

    master_comments_train_df = pd.read_csv('capstoneCommentsTrain.csv', encoding = "ISO-8859-1")
    sentiment(master_comments_train_df)

    print(master_comments_train_df)

    #master_comments_df.to_csv('capstoneCommentsTrain.csv', index=False) 
    #master_posts_df.to_csv('capstonePostsTrain.csv', index=False) 


if __name__ == "__main__":
    main()




