import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# see this:
# http://nycdatascience.com/nyc-concert-data-web-scraping-with-python/

# function to scrape info from a given link on site
def scrape(link):

    # parse webpage with BeautifulSoup
    text = requests.get(link).text
    soup = BeautifulSoup(text)
    
    
    # extract venue and genre(s) from <title>stuff|stuff|stuff|</title>
    # at top of html
    title = soup.title.string
    title = title.split(' | ')
    name = title[0]
    venue = title[1]
    genre = title[2]
    print "Event name =", name
    print "Venue =", venue 
    print "Kind =", genre
    
    
    ### Get Description
    description = soup.find_all("meta", {"name":"description"} )[0]["content"]
    print "Description =", description
    
    
    ### Get Address stuff
    street = soup.find_all("meta", {"property":"og:street-address"} )[0]["content"]
    lat = soup.find_all("meta", {"property":"og:latitude"} )[0]["content"]
    lon = soup.find_all("meta", {"property":"og:longitude"} )[0]["content"]
    locale = soup.find_all("meta", {"property":"og:locality"} )[0]["content"]
    region = soup.find_all("meta", {"property":"og:region"} )[0]["content"]
    zipc = soup.find_all("meta", {"property":"og:postal-code"} )[0]["content"]
    
    print "Address =", street, locale, region, zipc
    print "Lat, lon =", lat, lon
    

    ### Get event meta data
    metaData = soup.find_all("div", {"class":"MainColumn Event ", "id":"EventMetaData"} )
    spans = metaData[0].find_all("span")
    
    foundWhen = False
    foundPrice = False
    textPrice = 'none'
    for i, cont in enumerate(spans):
        #print "TEXT:",cont.text,"SIB:", cont.next_sibling, type(cont.text), type(cont.next_sibling)
        if (cont.text=="When:"):
            #print 'found when'
            when = cont.next_sibling.strip()
            foundWhen = True
        if (cont.text=="Price:"):
            #print 'found price'
            textPrice = cont.next_sibling.strip()
            foundPrice = True
            

            
    ### Perhaps do other parsing: event was listed today for a reason, perhaps an "every 4th Friday" thing
    if (not foundWhen):
        print "returning none"
        return None
        
    #print "price string =", textPrice
    

    
    ### Parse price
    
    # use regular expressions (re) to scrape multiple prices
    # ()    look for groups of the character sequence inside the brackets
    # \$    look for a dollar sign at the front (needs escape character \)
    # \d    look for decimal digit [0-9]
    # +     greedy, make longest sequence possible (match one or more of the preciding RE)
    # \.    look for '.' (needs escape character \)
    # ?     Causes the resulting RE to match 0 or 1 repetitions of the preceding RE. 
    #       ab? will match either 'a' or 'ab'. i.e. doesn't HAVE to match the thing immediately proceeding it
    
    dollarValues = re.findall('(\$?\d+\.?\d?\d?)', textPrice)
    
    # checks if price contains free
    if (textPrice.count('free') != 0) or (textPrice.count('Free') != 0) or (textPrice.count('FREE') != 0): 
        minprice = maxprice = 0.00
    elif len(dollarValues) == 0:
        minprice = maxprice = None
    else:
        for i in range(0, len(dollarValues)):
            dollarValues[i] = float(dollarValues[i].strip('$'))
        minprice = min(dollarValues)
        maxprice = max(dollarValues)
    if (maxprice != minprice):
        print "Price range =", minprice, "to", maxprice
    else:
        print "Price =", minprice
    
    print "When =", when

    """   
    # get time and date
    # find all "when" class divs
    time_date = soup.find('div', 'when').get_text()
    
    # regular expression to parse the time
    timeString = re.findall('(\d*:\d* .\.m\.)', time_date)
    if len(timeString) == 0:
        time = None
    else:
        time = timeString[0]
    print time
  

    # return list with relevant info
    return [venue, minprice, maxprice, neighborhood, address_full, time]
    """



# The code below searches all of today's listings
numDays = 1
for j in range(0, numDays):

    nEvents = 0
    
    # get string with date
    date = datetime.date.today() + datetime.timedelta(days = j) 
    dateString = date.strftime("%Y-%m-%d")
    print "DATE:"
    print dateString
    
    baseUrl = 'http://www.tucsonweekly.com/tucson/EventSearch?narrowByDate='
    
    # while loop to crawl over pages
    npageMax = 1000 # maximum possible number of pages of events: a huge number, and the code should break 
                    # before this

    
    # base URL for this date
    url = baseUrl + dateString
    
    for pageNum in xrange(1, npageMax):
        print "On page =", pageNum
    
        # parse webpage with BeautifulSoup
        if (pageNum>1):
            url = baseUrl + dateString + "&page=" + str(pageNum)
        
        text = requests.get(url).text  # get raw html
        soup = BeautifulSoup(text)     # input it into BeautifulSoup to parse it

    
        # get all "div" tags that corresond to a single event
        eventTags = soup.find_all('div', 'EventListing clearfix')
        print "There are", len(eventTags), "events on this page"
        nEvents += len(eventTags)
        
        # break out of loop over pages if no events found
        if (len(eventTags)<1):
            break
            
        # loop over each event and attempt to extract the html link for the page of the event
        for i, event in enumerate(eventTags):

            print "EVENT", i ,"START:"
        
            # find all the anchor ('a') tags within the 'div' tag for the evetn
            anchor_tags = event.find_all('a')
        
            # iterate over each anchor tag looking for the FIRST one that has a 'href' attribute
            # but does NOT have a 'class' attribute
            # NOTE: due to poor structure of Tucson Weekly event div's this may be the only way
            #       however it may not be robust/work for everything?
            isFound = False
            for j,mb in enumerate(anchor_tags):
                if (mb.has_attr('href') and (not isFound) and (not mb.has_attr('class')) ):
                    event_name = mb.get_text().strip() # this should be the event name! (type unicode)
                    event_link = mb.attrs['href']      # this should be the event webpage! (type string)
                    #print "Event name =", event_name
                    #print "Event link =", event_link
                    isFound = True
                    
            scrape(event_link)
            print "\n"
        
    print "There were", nEvents ,"events on", dateString




# parse webpage with BeautifulSoup
link = "http://www.tucsonweekly.com/tucson/light-bending-mind-blowing/Event?oid=4898248"
#link = "http://www.tucsonweekly.com/tucson/arizona-sonora-desert-museum/Event?oid=1107662"
#scrape(link)
