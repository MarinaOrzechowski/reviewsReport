# connect to MongoDB boaReviews table
# retrieve last added reviews for each publisher: trustpilot.com, depositaccounts.com, consumeraffairs.com
# remember their ids

# scrape reviews from each publisher until hit a review with saved id
# run through ML model to predict product
# add scraped reviews to MongoDB
# return True if success
# return False if something failed
import scrape
import dns
import pandas as pd
from pymongo import MongoClient
from sklearn.feature_extraction.text import CountVectorizer
import pickle
import string
import gender_guesser.detector as gender
d = gender.Detector()


######################################################################################
# connect to MongoDB and retrieve last added reviews for each publisher
######################################################################################
mypassw = "PowerMax300"

# Scrapes publishers sites and adds new reviews to boaReviews database.
# Does not return anything.
def updateDB():

    #connect to boaReviews database
    client = MongoClient("mongodb+srv://mishkice:"+mypassw+"@cluster0.t6imm.mongodb.net/boaReviews?retryWrites=true&w=majority")
    db = client["boaReviews"]
    collection = db["reviews"]
    df = pd.DataFrame(collection.find())
    del df['_id']
    print('Connected to database')

    # retrieve 
    publishers = ['trustpilot.com', 'bbb.org', 'depositaccounts.com','consumeraffairs.com']
    vocab = {}
    for source in publishers:
        result = list(collection.find( { 'source': source } ).sort([("datestamp", -1)]).limit(1))
        date = result[0]['datestamp']
        #date = datetime.strptime(date, '%Y-%m-%d')
        vocab[source] = date 
        
    print('Retrieved list of dates of last retrieved reviews for each site')

    
    df = scrape.scrapeData(vocab)
    print(df.head())
    ######################################################################################
    # Run data through the text classification model and fill out the 'product' field, gender
    ######################################################################################

    # add missing columns
    df['product'] = ''
    df['weekday'] = ''
    df['gender'] = None

    # load the model and vectorizer from disk
    print('Predicting product, gender, and weekday')
    modelLocation = 'finalized_model.sav'
    model = pickle.load(open(modelLocation, 'rb'))
    vectorizer = pickle.load(open("vectorizer.pickle", 'rb'))  

    stopBusinessWords = set(["customer", "manager", "office", "bank", "line", "america", "time", "money", "will", "boa"])
    punct = string.punctuation

    namesVocab = {'unknown': None,'andy': 'male', 'male':'male', 'female':'female', 'mostly_male':'male', 'mostly_female':'female'}
    
    for ind, row in df.iterrows():
        # predict product
        sentence = []
        text = row['text']
        for p in punct:
            text = text.replace(p, ' ')
            
        for w in text.split(' '):
            if w.lower() not in stopBusinessWords and len(w)>1:
                sentence.append(w.lower())
        sentence = ' '.join(sentence)
        prediction = model.predict(vectorizer.transform([sentence]))[0]
        df.at[ind, 'product'] = prediction

        prodVocab = {
            "business service":'Bank of America Business Services',
            'credit card': 'Bank of America Credit Cards',
            'credit': 'Bank of America Credit Cards',
            'certificate':'Bank of America CDs',  
            "car loan":'Bank of America Car Loans',          
            'equity':'Bank of America Home Equity' ,            
            "mortgage":'Bank of America Mortgages',   
            "morgage":'Bank of America Mortgages',
            'loan':'Bank of America Personal Loans',  
            'loans':'Bank of America Personal Loans',
            'prepaid':'Bank of America Prepaid Cards',         
            "savings":'Bank of America Savings',         
            'savings and cd':'Bank of America Savings & CDs' ,
            'customer service':'Bank of America Customer Service'
            }
        for ind, row in df.iterrows():
            for keyword in prodVocab.keys():
                if row.text.find(keyword) != -1:
                    df["product"][ind] = prodVocab[keyword]
        # predict gender from name
        name = row['name'].split(" ")[0].lower().capitalize()
        gender = namesVocab[d.get_gender(name)]    
        df.at[ind,'gender'] = gender

        # add weekday field
        date = pd.Timestamp(row['date'])
        df.at[ind, 'weekday'] = date.dayofweek

    ######################################################################################
    # Add scraped reviews to MongoDB
    ######################################################################################

    # delete from DB all reviews with dates in vocab (to avoid duplicates)
    for publisher in publishers:
        delete_query = { "date": vocab[publisher], 'source': publisher}
        x = collection.delete_many(delete_query)

    # insert new reviews
    client = MongoClient("mongodb+srv://mishkice:"+mypassw+"@cluster0.t6imm.mongodb.net/boaReviews?retryWrites=true&w=majority")
    db = client["boaReviews"]
    collection = db["reviews"]
    x = collection.insert_many(df.to_dict('records'))
    print('done')
    
