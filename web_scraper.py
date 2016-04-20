import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import psycopg2
import numpy as np

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
    address = ["og:street-address", "og:latitude", "og:longitude", "og:locality",
               "og:region", "og:postal-code"]
    addr_stuff = []
    for ad in address:
        result = soup.find_all("meta", {"property": ad})
        if (len(result)>0):
            addr_stuff.append(result[0]["content"])
        else:
            addr_stuff.append(None)
        
    #street = soup.find_all("meta", {"property":"og:street-address"} )[0]["content"]
    #lat = soup.find_all("meta", {"property":"og:latitude"} )[0]["content"]
    #lon = soup.find_all("meta", {"property":"og:longitude"} )[0]["content"]
    #locale = soup.find_all("meta", {"property":"og:locality"} )[0]["content"]
    #region = soup.find_all("meta", {"property":"og:region"} )[0]["content"]
    #zipc = soup.find_all("meta", {"property":"og:postal-code"} )[0]["content"]
    
    street = addr_stuff[0]
    lat = addr_stuff[1]
    lon = addr_stuff[2]
    locale = addr_stuff[3]
    region = addr_stuff[4]
    zipc = addr_stuff[5]
    
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
    if (not foundWhen or when == "Ongoing"):
        print "\n***********No event time:", description, "\n"
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
    price = None 
    if (maxprice != minprice):
        print "Price range =", minprice, "to", maxprice
        price = np.mean([minprice, maxprice]) #str(minprice) + " to " + str(maxprice)
    else:
        price = minprice
        print "Price =", minprice
    
    print "When =", when, "\n"
    
    return name, description, street + locale + region + zipc, price, when

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

### Create dataframe
columns = ['Name', 'Description', 'Price']
#['Name', 'Description', 'Address', 'Price', 'When']
df = pd.DataFrame(columns=columns)
print df.head()

### Connect to the tucson database (already created)
conn = psycopg2.connect(database="tucson", user="alex", host="/var/run/postgresql/", port="5432")
cursor = conn.cursor()
#temporary: delete everything
cursor.execute("DELETE FROM events;");
# reset auto increment to start at 1
cursor.execute("SELECT setval(pevent_id, 1) FROM events")


# The code below searches all of today's listings
numDays = 1
for j in range(0, numDays):

    nEvents = 0
    
    # get string with date
    date = datetime.date.today() + datetime.timedelta(days = j) 
    dateString = date.strftime("%Y-%m-%d")
    print "DATE:"
    print dateString, "\n"
    
    baseUrl = 'http://www.tucsonweekly.com/tucson/EventSearch?narrowByDate='
    
    # while loop to crawl over pages
    npageMax = 2000 # maximum possible number of pages of events: a huge number, and the code should break 
                    # before this

    
    # base URL for this date
    url = baseUrl + dateString
    ii=0
    for pageNum in xrange(1, npageMax):
        print "On page =", pageNum, "\n"
    
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
                    
            return_data = scrape(event_link)
            if (return_data is not None):
                name, description, addr, price, when = return_data
                
                # scrape when to just get time out
                
                # scrape description to look for dates/times and remove?
                
                # check if name is present in table yet
                df.loc[ii] = [name, description, price] #[name, description, addr, price, when]
                
                # playing with database
                
                ### DON'T LOOK IN FOURSQUARE DATABASE IF KIND=SPECIAL EVENT
                
                
                name = name.replace("'", "")
                description = description.replace("'", "")
                print name
                name = name.encode('ascii','ignore')
                description = description.encode('ascii','ignore')
                
                if (not price == None):
                    cmd = "INSERT INTO events(event_name, description, price) VALUES"
                    cmd +=" ('{0:s}', '{1:s}', {2:3.2f})".format(name, description, price)
                else:
                    cmd = "INSERT INTO events(event_name, description) VALUES"
                    cmd +=" ('{0:s}', '{1:s}')".format(name, description)
                print cmd
                cursor.execute(cmd)
                
                ii+=1
            print "\n"
        
    print "There were", nEvents ,"events on", dateString
    print df.head(15)


conn.commit()
conn.close()
print "Closed database successfully"
# parse webpage with BeautifulSoup
#link = "http://www.tucsonweekly.com/tucson/light-bending-mind-blowing/Event?oid=4898248"
#link = "http://www.tucsonweekly.com/tucson/arizona-sonora-desert-museum/Event?oid=1107662"
#scrape(link)
