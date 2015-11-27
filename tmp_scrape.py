import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# see this
# http://nycdatascience.com/nyc-concert-data-web-scraping-with-python/

# function to scrape info from a given link on site
def scrape(link):

    #parse webpage with BeautifulSoup
    text = requests.get(link).text
    text = BeautifulSoup(text)
    
    # extract venue and genre(s) from <title>stuff|stuff|stuff|</title>
    # at top of html
    title = text.title.string
    print title
    title = title.split(' | ')
    print title
    venue = title[1]
    print venue
    genre = title[2].split(', ')
    print genre
    
    # get price
    price = text.find('div', 'price')
    if price.string != None:
        price = price.string.lower()
    else:
        price = ''
    print price, type(price)
    
    # use regular expressions (re) to scrape multiple prices
    dollarValues = re.findall('(\$\d+\.?\d?\d?)', price)
    print dollarValues
    
    
    # get time and date
    # find all "when" class divs
    time_date = text.find('div', 'when').get_text()
    
    # regular expression to parse the time
    timeString = re.findall('(\d*:\d* .\.m\.)', time_date)
    if len(timeString) == 0:
        time = None
    else:
        time = timeString[0]
    print time
  
    
    # get min and max concert price depending on price &amp; format
    if price.count('free') != 0: # checks if price contains free
        minprice = maxprice = 0.00
    elif len(dollarValues) == 0:
        minprice = maxprice = None
    else:
        for i in range(0, len(dollarValues)):
            dollarValues[i] = float(dollarValues[i].strip('$'))
        minprice = min(dollarValues)
        maxprice = max(dollarValues)
    
    # get neighborhood
    # find all "neighborhood" class divs
    neighborhood = text.find('div', 'neighborhood').get_text()
    print neighborhood
    neighborhood = re.sub('(\\n\\n *)', '', neighborhood)
    print neighborhood
    neighborhood = re.sub('( *\\n)$', '', neighborhood)
    print neighborhood
    
    
    # get address info
    # find all "address" class divs
    address = text.find('div', 'address').get_text()
    print address
    address = re.split('(?:\\xa0)?\\n +|\D+$', address)
    print address
    street = address[1]
    city = address[2]
    zipcode = address[3]
    phone = address[4]
    address_full = ', '.join([street, city, zipcode])
    
    # return list with relevant info
    return [venue, minprice, maxprice, neighborhood, address_full, time]
    

link = "http://www.villagevoice.com/event/john-pizzarelli-and-jessica-molaskey-7532546"

#scrape(link)


numDays = 1
for j in range(0, numDays):

    # get string with date
    date = datetime.date.today() + datetime.timedelta(days = j) 
    dateString = date.strftime("%Y-%m-%d")
    print "DATE:"
    print dateString
    
    # parse webpage with BeautifulSoup
    url = 'http://www.tucsonweekly.com/tucson/EventSearch?narrowByDate=' + dateString
    text = requests.get(url).text  # get raw html
    soup = BeautifulSoup(text)     # input it into BeautifulSoup to parse it

    
    # get whole event div
    eventTags = soup.find_all('div', 'EventListing clearfix')[1:]
    print type(eventTags)
    
    for i, event in enumerate(eventTags):
        #if (i>12):
        #    print event

        print "EVENT START", i
        maybe = event.find_all('a')
        print len(maybe), "a's", type(maybe)
        isFound = False
        for j,mb in enumerate(maybe):
            print j#, mb, type(mb)
            if (mb.has_attr('href') and (not isFound) and (not mb.has_attr('class')) ):
                print mb.get_text()    # this is the event name!
                print mb.attrs['href'] # this is the event webpage!
                isFound = True
        print "\n"
    print len(eventTags), "events"
    
#text = requests.get(link).text

