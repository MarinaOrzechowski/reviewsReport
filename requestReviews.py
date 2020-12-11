# connect to MongoDB boaReviews table
# retrieve last added reviews for each publisher: trustpilot.com, depositaccounts.com, consumeraffairs.com
# remember their ids
# scrape reviews from each publisher until hit a review with saved id
# run through ML model to predict product
# add scraped reviews to MongoDB
# return True if success
# return False if something failed

import dns
import pandas as pd
from pymongo import MongoClient
from sklearn.feature_extraction.text import CountVectorizer
import pickle


######################################################################################
# connect to MongoDB and retrieve last added reviews for each publisher
######################################################################################
#change password on yours
client = MongoClient("mongodb+srv://mishkice:<Password>@cluster0.t6imm.mongodb.net/boaReviews?retryWrites=true&w=majority")
db = client["boaReviews"]
collection = db["reviews"]
publishers = ['trustpilot.com', 'bbb.org', 'depositaccounts.com','consumeraffairs.com']



######################################################################################
# Run data through the text classification model and fill out the 'product' field
######################################################################################

# load the model and vectorizer from disk
nodelLocation = 'finalized_model.sav'
model = pickle.load(open(nodelLocation, 'rb'))
vectorizer = pickle.load(open("vectorizer.pickle", 'rb'))  

for ind, row in df.iterrows():
    text = row['text']
    df['product'] = model.predict(vectorizer.transform([text]))[0]

#x = col.insert_many(df.to_dict('records'))
