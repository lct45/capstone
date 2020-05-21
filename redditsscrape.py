import yaml
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
    'topic': [],
    "author" : [],
    "comms_num": [],
    "created": [],
    "body":[]
    }
master_comments = { 
    "id":[], 
    'post_id':[],
    'parent_id': [],
    'post_topic':[],
    "comms_num": [],
    "body":[],
    "sentiment": []
    }

negList=[]
posList=[]
accuracyList=[]

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
    posts_df.insert(3, 'deleted comms', 0)
    posts_df.insert(3, 'top level comms', 0)
    posts_df.insert(3, 'nested comms', 0)
    for ident in posts_df.index:
        submission = reddit.submission(id=ident)
        #only pull top level comments, not replies to replies for now
        submission.comments.replace_more(limit=None)
        counter = 0
        topcounter = 0
        topic = posts_df.at[ident, 'topic']
        for comment in submission.comments.list():        
            #need to make sure its not picking up comments from OP
            counter +=1
            if 't3_' in comment.parent_id:
                topcounter +=1
            if comment.is_submitter == False and comment.body != '[removed]' and comment.body != '[deleted]':
                master_comments['id'].append(comment.id)
                master_comments['post_id'].append(ident)
                master_comments['parent_id'].append(comment.parent_id)
                master_comments['post_topic'].append(topic)
                master_comments['comms_num'].append(submission.num_comments)
                master_comments['body'].append(normalizeText(comment.body))
                master_comments['sentiment'].append('blank')
        posts_df.at[ident, 'deleted comms'] = submission.num_comments-counter
        posts_df.at[ident, 'top level comms'] = topcounter
        posts_df.at[ident, 'nested comms'] = counter-topcounter


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

def evaluation(df, col):
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for index in df.index:
        if df.at[index, col] == df.at[index, 'sentiment']:
            if df.at[index, col] == 'positive':
                tp += 1
            else:
                tn += 1
        else:
            if df.at[index, col] == 'positive':
                fp += 1
            else:
                fn += 1
    total = len(df.index)
    print('the number of correctly evaluated posts is {}'.format(tp+tn))
    print('the number of incorrect posts is {}'.format(fp+fn))
    #print('the number of true positive  is {}'.format(tp))
    #print('the number of true negative  is {}'.format(tn))
    #print('the number of false positive  is {}'.format(fp))
    #print('the number of false negative  is {}'.format(fn))
    #print('supposed to have {} positive but have {} positive'.format((tp+fn), (tp+fp)))
    #print('supposed to have {} negative but have {} negative'.format((tn+fp), (tn+fn)))
    print('supposed to have {} negative but have {} negative'.format((tn+fp)/total, (tn+fn)/total))
    print('supposed to have {} positive but have {} positive'.format((tp+fn)/total, (tp+fp)/total))
    print('out of {}, we correctly classified {}'.format(len(df.index), (tp+tn)/(len(df.index))))
    accuracyList.append((tp+tn)/(len(df.index)))
    negList.append(tn+fn)
    posList.append(tp+fp)

def parentsent(parent_id, df, postdf):
    if 't3_' in parent_id:
        test = parent_id.replace('t3_', '')
        parent_sent = postdf.at[test, 'sentiment']
    else:
        test = parent_id.replace('t1_', '')
        try:
            parent_sent = df.at[test, 'sentiment']
        except:
            parent_sent = 'neutral'
    return parent_sent
        

def sentiment(df, postdf):
    df.insert(len(df.columns)-1, 'new sent', 'blank')
    df.insert(len(df.columns)-1, 'w par sent', 'blank')

    for index in df.index:
        blob = TextBlob(df.at[index, 'body'])
        pol = blob.sentiment.polarity
        parsent = parentsent(df.at[index, 'parent_id'], df, postdf)
        if pol > 0:
            df.at[index, 'new sent'] = 'positive'

            df.at[index, 'w par sent'] = 'positive'

        elif pol < 0:
            df.at[index, 'new sent'] = 'negative'

            if parsent == 'negative':
                df.at[index, 'w par sent'] = 'positive'
            else:
                df.at[index, 'w par sent'] = 'negative'

        else:
            df.at[index, 'new sent'] = 'neutral'

            if parsent == 'negative':
                df.at[index, 'w par sent'] = 'negative'
            else:
                df.at[index, 'w par sent'] = 'positive'

    df.to_csv('sentimentized.csv', index=False)        
    evaluation(df, 'new sent')
    #evaluation(df, 'w par sent')


def stats(df):
    values = {}
    for val in df['post_topic'].unique():
        temp = df[df['post_topic']== val]
        i = temp['sentiment'].value_counts()
        pos = i['positive']
        neg = i['negative']
        try:
            neut = i['neutral']
        except:
            neut = 0
        total = pos+neg+neut
        values[val] = [pos, neg, neut, total]
    posdf = df[df['sentiment']== 'positive']
    negdf = df[df['sentiment']=='negative']
    test = posdf['post_topic'].value_counts()
    test2 = negdf['post_topic'].value_counts()
    for i in values:
        print('for topic {} we had {} total comments, {} positive, {} negative and {} neutral'.format(i, values[i][3], values[i][0], values[i][1], values[i][2]))
        print('the proportion of positive was {} and proportion of negative {}'.format(values[i][0]/values[i][3], values[i][1]/values[i][3]))
        print('and for positive posts in {} we had {}'.format(i, test[i]))
        print('and for negative posts in {} we had {}'.format(i, test2[i]))

    
def controlstat(df):
    uniques = len(df['post_id'].unique())
    totals = len(df.index)
    posdf = df[df['sentiment']== 'positive']
    negdf = df[df['sentiment']=='negative']
    poslen = len(posdf.index)
    neglen = len(negdf.index)
    print('for control we had {} posts with {} total comments'.format(uniques, totals))
    print('we had {} total positive comments and {} total negative comments'.format(poslen, neglen))
    print('on average, there were {} positive comms and {} negative comms per post'.format(poslen/uniques, neglen/uniques))




        

def nbclassify(dftest, dftrain, postdf, control):
    dftrain = dftrain[['body','sentiment']]
    tuples = [tuple(x) for x in dftrain.to_numpy()]
    cl = NaiveBayesClassifier(tuples)
    #cl.show_informative_features(10)
    
    print('base case')
    for index in control.index:
        blob = TextBlob(dftest.at[index, 'body'], classifier=cl)
        prob = blob.classify()
        control.at[index, 'sentiment'] = prob
    controlstat(control)
    print('\n\n')
    print('just NB classifier')
    for index in dftest.index:
        blob = TextBlob(dftest.at[index, 'body'], classifier=cl)
        prob = blob.classify()
        dftest.at[index, 'sentiment'] = prob
    stats(dftest)
    controlstat(dftest)

    print('\n\n')
    print('with parent into consideration')
    for index in dftest.index:
        parentid = dftest.at[index, 'parent_id']
        parsent = parentsent(parentid, dftest, postdf)
        
        if 't3_' in parentid:
            if prob == parsent:
                prob = 'positive'
            elif parsent != 'neutral':
                prob = 'negative'
        else:
            if prob == 'positive' and parsent != 'neutral':
                prob = parsent
            elif prob == 'negative' and parsent != 'neutral':
                if parsent == 'negative':
                    prob = 'positive' 
                else:
                    prob = 'negative'
            if prob == 'neutral':
                print('neutrality shows up here')

        dftest.at[index, 'sentiment'] = prob
    stats(dftest)
    controlstat(dftest)


def nbsentiment(dftest, dftrain):
    dftrain = dftrain[['body','sentiment']]
    tuples = [tuple(x) for x in dftrain.to_numpy()]
    cl = NaiveBayesClassifier(tuples)
    dftest.insert(len(dftest.columns)-1, 'new sent', 'blank')

    for index in dftest.index:
        #prob = cl.classify(dftest.at[index, 'body'])
        blob = TextBlob(dftest.at[index, 'body'], classifier=cl)
        prob = blob.classify()
        #pol = blob.sentiment.polarity
        #if pol > .05:
        #    prob = 'positive'
        #else:
        #    prob = 'negative'
        dftest.at[index, 'new sent'] = prob
    dftest.to_csv('sentimentizednaivebayes.csv', index=False)   
    #dftest = dftest[['body','sentiment']]
    #test_tuples = [tuple(x) for x in dftest.to_numpy()]
    #print('accuracy of {}'.format(cl.accuracy(test_tuples)))
    evaluation(dftest, 'new sent')


def main():
    reddit = praw.Reddit(client_id='glYFKzXUunPN0w',
                     client_secret='YYVttwTqQePKNqE5RKu3kxX6mNE',
                     user_agent='APP_NAME')
    subreddit = reddit.subreddit('cscareerquestions')
    
    #searches(subreddit)

    #this was pulling posts and creating post data grame
    #master_posts_df = pd.DataFrame(master_posts)
    #master_posts_df.to_csv('fullposts.csv', index=False)

 

    #pulling comments from the posts CSV, only needs to be done once
    #posts_train = master_posts_df.iloc[:19, :]
    #processcomments(reddit, posts_train)
    #master_comments_df = pd.DataFrame(master_comments)
   #getting posts from already created CSV files
    master_posts_df = pd.read_csv('capPostSent.csv', index_col = 'id')
    master_posts_df.sort_values(by='id', inplace= True)
    comments_train_df = pd.read_csv('capstoneCommentsTrainNB.csv', index_col = 'id', encoding = "ISO-8859-1")
    #print('OLD SENTIMENT HERE LADIES')
    #sentiment(master_comments_train_df, master_posts_df)
    comments_train_df = comments_train_df.sample(frac=1).reset_index(drop=True)
    size = int(len(comments_train_df.index)/6)
    print('Naive Bayes')


    #processcomments(reddit, master_posts_df)
    #master_posts_df.to_csv('updatedPosts.csv', index=False)
    #master_comments_df = pd.DataFrame(master_comments)
    master_comments_df = pd.read_csv('gendercommentsfull.csv')
    control_df = pd.read_csv('controlcomms.csv')

    nbclassify(master_comments_df, comments_train_df, master_posts_df, control_df)

    for i in range(1,7): #change this back to 10 later
        print('Fold number {}\n'.format(i))
        if i == 1:
            dftest = comments_train_df.iloc[:size, :]
            dftrain = comments_train_df.iloc[size:, :]
        elif i > 1 and i < 6:
            last = i-1
            dftest = comments_train_df.iloc[size*last:size*i, :]
            dftrain1 = comments_train_df.iloc[:size*last, :]
            dftrain2 = comments_train_df.iloc[size*i:]
            frames = [dftrain1, dftrain2]
            dftrain = pd.concat(frames)
        else:
            dftest = comments_train_df.iloc[size*5:, :]
            dftrain = comments_train_df.iloc[:size*5, :]
        nbsentiment(dftest, dftrain)
   
    print('on avrage we had {} negative posts'.format(sum(negList)/len(negList)))
    print('on average we had {} positive posts'.format(sum(posList)/len(posList)))
    print('average accuracy {} '.format(sum(accuracyList)/len(accuracyList)))
    #master_comments_df.to_csv('gendercommentsfull.csv', index=False) 
    #master_posts_df.to_csv('capstonePostsTrain.csv', index=False) 


if __name__ == "__main__":
    main()




