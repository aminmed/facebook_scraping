from facebook_scraper import get_posts
import pymongo
import json 

def connect_to_db (config_file = ''):
    ''' 
    Create a connection to a mongodb database
    url and credentials are in config file 
    '''   
    with open(config_file) as file:
        lines = file.readlines()
        conn_str = lines[0].split('=')[-1].strip()
        username = lines[1].split('=')[-1].strip()
        password = lines[2].split('=')[-1].strip()
        database = lines[3].split('=')[-1].strip()

    if(len(conn_str) == 0):
        conn_str = "mongodb+srv://"+username+":"+password+"@cluster0.toyhe.mongodb.net/"+database+"?retryWrites=true&w=majority"
    conn_str = conn_str.strip()
    client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    try:
        print("connected to {0} ... ",conn_str)
    except Exception:
        print("Unable to connect to the server.")

    return {'client': client, 'db': database }

def extract_data_from_info(post_info):
    ''' 
    Given one post_info dictionnary, this method return 
    its text content, comments, images_urls related to 
    the post.
    it return dictionnary with three filds : post_text, comments (only the texts), images url
    
    '''
    post = {}
    post['post_text'] = post_info['post_text']
    post['images']    = json.dumps(post_info['images']) 

    #retrieving all comments related to the post in a list !
    comments = []
    for comment in post_info['comments_full']:
        comments.append(comment['comment_text'])
    
    post['comments']= json.dumps(comments)
    
    return post

def is_post_related_to_subject(post_text = "", subject = ""):
    ''' 
    a method to test if a post is related to a given subject.
    return a boolean value
    '''   
    subject_list = subject.lower().split(' ')
    post_text_list = post_text.lower().split(' ')
    nb_words = len(subject_list)
    count = 0
    for word in subject_list:
        if(word in post_text_list):
            count += 1 
    return ( (count // nb_words) > 0.8 ) 

def get_query_infos(config_query):

    with open(config_query) as file:
        lines = file.readlines()
        page = lines[0].split('=')[-1].strip()
        subject = lines[1].split('=')[-1].strip()
        max_posts = lines[2].split('=')[-1].strip()
        verbose = lines[3].split('=')[-1].strip()

    return {'page':page, 'subject': subject, 'max_posts':max_posts, 'verbose': verbose}

if(__name__ == '__main__' ):
    query = get_query_infos(config_query='./config_query')
    channel_str =query['page']
    subject = query['subject']
    max_posts_consulted = int(query['max_posts'])
    verbose = (False,True)[query['verbose'] == 'True']

    # connect to mongodb database in ATLAS
    connection = connect_to_db(config_file='config_mongodb')
    client = connection['client']
    db = client[connection['db']]

    posts_number = 0
    posts_inserted_to_database = 0
    for post_info in get_posts(channel_str, pages=3, options={"comments": 30, "reactors": False, "progress":False, "posts_per_page": 10}):
        posts_number += 1
        if(verbose):
            print("- page : {0}  number of posts consulted {1} ".format( channel_str,posts_number))
            print("- {0} posts related to subject found".format(posts_inserted_to_database))

        if(is_post_related_to_subject(post_text=post_info['post_text'], subject=subject)):
            # post_info contains alot of data for which we are not looking for
            # extract_data gives a dict with the only post_text, comments, and images 
            post = extract_data_from_info(post_info=post_info)
            # insert the post retrieved in the database 
            db.reviews.insert_one(post)
            posts_inserted_to_database += 1
        if(posts_number > max_posts_consulted):
            break

    # close connection to database 
    client.close()
