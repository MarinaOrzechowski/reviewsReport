from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
from time import sleep
from datetime import datetime
import pandas as pd
import re
import string


def scrapeData(vocab):
    df = pd.DataFrame(columns=('name', 'date', 'rating', 'text', 'boaDate', 'boaText', 'source', 'responded', 'timeRetrieved', 'htmlId'))
    print('Empty dataframe created')

    ############################################################################################
    # TrustPilot
    ############################################################################################
    print('.....Scraping TrustPilot.com')
    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    url = 'https://www.trustpilot.com/review/www.bankofamerica.com'

    temp = 2
    driver.implicitly_wait(5)
    driver.maximize_window()
    driver.get(url)
    xpath1 = '/html/body/div[4]/div[3]/div/div/div[3]/button'
    xpath2 = '/html/body/div[3]/a'
    # close accept cookies tab
    driver.implicitly_wait(5)

    # close Covid notification tab
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath2))).click()
    except:
        pass
    sleep(2)
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath1))).click()
    except TimeoutException:
        pass
    sleep(2)

    # close Covid notification tab
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath2))).click()
    except:
        pass
        
    sleep(1)
    flag = True
    while flag:   
        try:          
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            for block in soup.find_all("article", class_='review'):
                htmlId = block.get('id')


                timeRetrieved = datetime.now()
                date = block.find('time', class_='review-date--tooltip-target').get('datetime').split('T')[0]
                date = datetime.strptime(date, '%Y-%m-%d')
                #check if review was previously scraped
                if date < vocab['trustpilot.com']:
                    print('found matching review')
                    flag = False
                    break
                else:
                    name = block.find('div', class_='consumer-information__name').text.strip()
                    stars = block.find('div', class_='star-rating star-rating--medium').find('img').get('alt').split(' ')[0]
                    text = block.find('p', class_='review-content__text')
                    if text:
                        text = text.text.strip()
                    else:
                        text = block.find('a', class_='link link--large link--dark').text.strip()

                    df = df.append({'name' : name , 'date' : date, 'rating': stars, 'text': text, 'boaDate': None, \
                                    'boaText': None, 'source': 'trustpilot.com', 'timeRetrieved':timeRetrieved, \
                                    'htmlId': htmlId, 'responded':False} , ignore_index=True)        
            if flag:
                next_page_btn = driver.find_element_by_partial_link_text("Next page")
                # open next page
                try:
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Next page'))).click()
                except  StaleElementReferenceException:
                    sleep(5)
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Next page'))).click()
                print('.........Opened page', temp)
                temp += 1
                sleep(5)
            else: 
                print('Done with Trustpilot.com')
                break
        except:
            print("No more pages left")
            break
    print('processed all pages')        


    ############################################################################################
    # BBB.org
    ############################################################################################
    print('.....Scraping BBB.org')
    # press load more until reach end of the page
    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    url = 'https://www.bbb.org/us/nc/charlotte/profile/bank/bank-of-america-0473-100421/customer-reviews'
    driver.implicitly_wait(5)
    driver.maximize_window()
    driver.get(url)

    xpath = '/html/body/div[2]/div[2]/div/button'
    css_selector = 'button.MuiButton-root:nth-child(2)'


    try:
        # close cookies notification
        myElem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        myElem.click()
    except TimeoutException:
        pass
    driver.implicitly_wait(15)

    times = 2
    while times>0:   
        try:   
            # load more reviews
            myElem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
            myElem.click()
            print('.........Loaded more reviews')
            times -= 1
            sleep(5) # otherwise spinning circle blocks the button
        except TimeoutException:
            print("Done loading reviews")
            break    

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')
    for block in soup.find_all("div", class_='MuiGrid-root styles__Review-sc-1azxajg-0 fyMiFZ dtm-review MuiGrid-container'):
        stars = block.find_all(d='M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z')
        stars = len(stars)
        date = block.find("p", class_='MuiTypography-root Typography-y2r0fa-0 kpIiVF MuiTypography-body2').text
        date = datetime.strptime(date, '%m/%d/%Y')
        name = block.find('p', class_='MuiTypography-root Name-t42m9k-0 kSwwPu MuiTypography-body2').text
        text = block.find_all('div', class_='MuiTypography-root Text-sc-12c66pm-0 fgbKlJ MuiTypography-body2')
        timeRetrieved = datetime.now()
        responded = False
        
        if len(text)>1:
            boaDate = block.find('p', class_='MuiTypography-root Date-sc-8slhbi-0 kEubpt MuiTypography-body1').text
            boaText = text[1].text
            responded = True
        else:
            boaDate = None
            boaText = None
        
        #check if review was previously scraped
        if date < vocab['bbb.org']:
            print('found matching review')
            flag = False
            break
        else:
            review = text[0].text
            df = df.append({'name' : name , 'date' : date, 'rating': stars, 'text': review, 'boaDate': boaDate, \
                                    'boaText': boaText, 'source': 'bbb.org', 'timeRetrieved':timeRetrieved, \
                                    'htmlId': name+review[:10], 'responded':responded} , ignore_index=True) 
    ############################################################################################
    # DepositAccounts.com
    ############################################################################################
    print('.....Scraping DepositAccounts.com')

    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    url = 'https://www.depositaccounts.com/banks/bank-of-america.html'

    driver.implicitly_wait(5)
    driver.maximize_window()
    driver.get(url)

    readMoreClassName = 'textExpand'

    # click 'View more'
    try:    
        viewMoreBtn = driver.find_element_by_partial_link_text("View MORE")
        viewMoreBtn.click()
    except TimeoutException:
        print("Couldn't open all reviews page")

    sleep(5)

    # expand all reviews
    # more_buttons = driver.find_elements_by_class_name(readMoreClassName)
    # for x in range(len(more_buttons)):
    #     if more_buttons[x].is_displayed():
    #         driver.execute_script("arguments[0].click();", more_buttons[x])
    #         time.sleep(1)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')
    starClassRe = re.compile('^stars')

    for block in soup.find_all("div", class_='bankReviewContainer'):
        title = block.find('h3').text
        
        stars = block.find('div', {"class" : starClassRe}).get('class')
        stars = int(stars[1][-1])
        
        name = block.find('span', itemprop='author').text
        date = block.find('span', itemprop='datePublished').get('datetime')
        y, m, d = date.split('-')
        date = '-'.join([y, m, d])
        date = datetime.strptime(date, '%Y-%m-%d')
        text = block.find('p', itemprop='description').text
        review = title+' '+text
        
        timeRetrieved = datetime.now()
        htmlId = block.find('div', class_='bankReview').get('id')
        if date < vocab['depositaccounts.com']:
            break
        else:
            df = df.append({'name' : name , 'date' : date, 'rating': stars, 'text': review, 'boaDate': None, \
                                    'boaText': None, 'source': 'depositaccounts.com', 'timeRetrieved':timeRetrieved, \
                                    'htmlId': htmlId, 'responded':False} , ignore_index=True) 
        

    ############################################################################################
    # ConsumerAffairs.com
    ############################################################################################
    print('.....Scraping ConsumerAffairs.com')

    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    url = 'https://www.consumeraffairs.com/finance/bofa.html'

    driver.implicitly_wait(5)
    driver.maximize_window()
    driver.get(url)

    monthVocab = {'jan': 1, 'feb': 2, 'march':3 , 'april':4, 'may': 5, 'june':6, 'july':7 , 'aug':8, 'sept':9 ,'oct':10, 'nov': 11,'dec':12}
    page = 2
    flag = True
    while flag:   
        try:
            
            #expend all reviews
            more_buttons = driver.find_elements_by_partial_link_text('Read full review')

            for x in range(len(more_buttons)):
                if more_buttons[x].is_displayed():
                    driver.execute_script("arguments[0].click();", more_buttons[x])
                    time.sleep(1)
            # process data on current page        
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            for block in soup.find_all("div", class_='rvw js-rvw'):

                stars = block.find('meta', itemprop = 'ratingValue').get('content')
                stars = int(stars)

                user = block.find('strong', itemprop = 'author').text
                name = user.split(' of ')

                date = block.find('span', class_ = 'ca-txt-cpt').text.split(': ')[1]
                date = date.replace('.', '').replace(',', '').lower()
                m, d, y = date.split(' ')
                m = str(monthVocab[m])
                date = '-'.join([y, m.zfill(2), d.zfill(2)])
                date = datetime.strptime(date, '%Y-%m-%d')

                text = block.find('div', class_ = 'rvw-bd').find_all('p')[1].text
                timeRetrieved = datetime.now()
                htmlId = block.get('id')
                if date < vocab['consumeraffairs.com']:
                    flag = False
                    break
                else:
                    df = df.append({'name' : name , 'date' : date, 'rating': stars, 'text': text, 'boaDate': None, \
                                        'boaText': None, 'source': 'consumeraffairs.com', 'timeRetrieved':timeRetrieved, \
                                        'htmlId': htmlId, 'responded':False} , ignore_index=True)
            if flag:
                next_page_btn = driver.find_element_by_partial_link_text("Next")
                # open next page
                try:
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Next'))).click()
                except  StaleElementReferenceException:
                    sleep(5)
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Next'))).click()
                print('.........Opened next page', page)
                page += 1
        except:
            print("No more pages left")
            break
    print('processed all pages')  

    return df