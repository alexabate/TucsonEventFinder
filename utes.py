"""Utility functions

"""

import foursquare
import difflib
import urllib2
import json
import numpy as np
from nltk.tokenize import word_tokenize



# Foursquare access 
CLIENT_ID = "E31UHYC4XENVIJJ5PLTG2PF4R414EHYZSP5XZU3430KF1PCL"
CLIENT_SECRET = "SMB0GPZQFGDMU1YQJ1FYLCBGF4ZAO0PWN4COIIWPQKVMGQY5"
VERSION = "20160401"

# Keywords (to be used case insensitive/plural insensitive)
DESCRIPTORS = []
SERVICES = {'beer': ['beer', 'ipa', 'ale', 'lager', 'alcohol', 'craft beer', 'bar', 'draft'], 
            'wine': ['wine','alcohol', 'bar'],  
            'liquor': ['margaritas', 'cocktails', 'vodka', 'tequila', 'full bar'], 
            'coffee': ['coffee'], 
            'food': ['breakfast', 'lunch', 'dinner', 'burgers', 'sandwiches', 'tacos', 'pizza', 'cafe',
                     'restaurant'] }
            

def convert_bit_array_to_decimal_rec(bit_array, x=0):
    """Convert arbitrary length bit array to decimal integer"""
    length_array = len(bit_array)
    
    if length_array>1:
        if (bit_array[0]>0):
            x += pow(2, length_array-1)
        return convert_bit_array_to_decimal_rec(bit_array[1:], x)
    else:
        if (bit_array[0]>0):
            x += 1
        return x
            
    
def convert_bit_array_to_decimal(bit_array):
    """Convert arbitrary length bit array to decimal integer"""
    decimal_int = 0
    ii = 0
    for i in np.arange(-(len(bit_array)), 0)*-1-1:
        if bit_array[ii]>0:
            decimal_int += pow(2.,i)
        ii+=1
    return int(decimal_int)
    
    
def convert_decimal_to_bit_array(dec):
    """Convert decimal integer to bit array"""
    
    bit_array = [int(x) for x in list('{0:0b}'.format(dec))]
    return bit_array
    

def getVenue(lat, lon, name, radius=300, addr=''):
    """Return closest venue in foursquare Venue database to lat, lon within radius 
    
       @param lat       latitude in degrees
       @param lon       longitude in degrees
       @param name      name of venue
       @param radius    radius away from lat, lon in meters
       
       returns 'hours_id' and 'service_flag' (both are decimal integers corresponding to bit arrays)
       also returns 'rating' (float) and 'likes' (integer) and 'venue_type' (list of strings)
       ready to be added to the database
       
       nix returning 'description' for now
    
    """
    # Construct the client object
    client = foursquare.Foursquare(CLIENT_ID, CLIENT_SECRET, redirect_uri='http://fondu.com/oauth/authorize')

    # Return all venues within radius of lat,lon
    ll = str(lat) + "," + str(lon)
    radius = str(radius)
    venues = client.venues.search(params={'v': VERSION, 'll': ll, 'intent': 'browse', 
                                      'radius': radius, 'limit': 100 })["venues"]
    # Returns a list of dictionaries, each is a "compact venue"
    print "Returned", len(venues) , "venues within", radius ,"meters"
    print venues[0]
    
    # pull out just venue name and its distance from lat, lon
    venue_deets = [(ven["name"], ven["location"]["distance"], ven["location"]["address"]) for ven in venues]
    
    # sort by distance away
    venue_deets = sorted(venue_deets, key=lambda x: x[1])
    venue_names = [x[0] for x in venue_deets]
    venue_addr = [x[2] for x in venue_deets]
    print venue_names
    
    # grab the "foursquare" version of the name
    if name in venue_names:
        # name supplied exactly matches foursquare name
        fs_name = name
    else:
        # look for close matches to supplied name
    
        # defaults set: returns a max of 3 matches with minimum score of 0.6 in similarity
        fs_name = difflib.get_close_matches(name, venue_names, n=3, cutoff=0.5)
        print fs_name
        
        if len(fs_name)<1:
            # hopefully this doesn't happen!
            #raise ValueError("ERROR: venue not found")
            # match on address instead
            add_name = difflib.get_close_matches(addr, venue_addr, n=3, cutoff=0.5)
            print add_name
            return -1
        elif len(fs_name)>1:
            # if more than one match returned take closest venue
            dists = [venue_deets[venue_names.index(n)][1] for n in fs_name]
            fs_name = fs_name[dists.index(min(dists))] # return closest
        else:
            fs_name = fs_name[0]
        
        
    # details of desired venue
    print "Name given =", name
    print "Name in foursquare =", fs_name
    print "Distance from original lat, long =", venue_deets[venue_names.index(fs_name)][1],"meters"
    desired_venue_id = [ven for ven in venues if ven["name"]==fs_name][0]["id"]

    
    # Now get "complete venue" information, that has more details on venue properties
    venue_url = "https://api.foursquare.com/v2/venues/" + desired_venue_id
    venue_url += "?client_id=" + CLIENT_ID
    venue_url += "&client_secret=" + CLIENT_SECRET
    venue_url += "&v=" + VERSION
    venue_url += "&m=foursquare"

    complete_venue = json.load(urllib2.urlopen(venue_url))["response"]["venue"]
    
    
    # fields that help grab pertinent information
    descriptors = ['phrases', 'categories', 'attributes', 'tags', 'tips']

    words = ''
    venue_type = []
    for desc in descriptors:
        if desc in complete_venue:
            field = complete_venue[desc] 
            
            # scan over phrases field
            if desc=='phrases':
                for f in field:
                    print "printing from 'sample'"
                    if 'sample' in f:
                        if 'text' in f['sample']:
                            print f['sample']['text'], type(f['sample']['text'])
                            words += f['sample']['text'] + ' '
                    print "printing from 'phrase'"
                    if 'phrase' in f:
                        print f['phrase'], type(f['phrase'])
                        words += f['phrase'] + ' '
                        
            # scan over categories field
            if desc=='categories':
                for f in field:
                    if 'name' in f:
                        print f['name'], type(f['name'])
                        words += f['name'] + ' '
                        venue_type.append(f['name'])
                        
            # scan over attributes field
            if desc=='attributes':
                if 'groups' in field:
                    gr = field['groups']
                    for f in gr:
                        if 'name' in f:
                            print f['name'], type(f['name'])
                            words += f['name'] + ' '
            
            # scan over tags field
            if desc=='tags':
                for f in field:
                    print f, type(f),
                    words += f + ' '
                print ''
            
            
            # scan over tips field
            if desc=='tips':
                if 'groups' in field:
                    gr = field['groups']
                    for group in gr:
                        if 'items' in group:
                            for item in group['items']:
                                if 'text' in item:
                                    print item['text'], type(item['text'])
                                    words += item['text'] + ' '
            print ''
            
    # scrape all words for things indicating beer, coffee, food, liquor, wine
    words = word_tokenize(words)
    words = [x.lower() for x in words]
    
    service_flag = [0,0,0,0,0]
    print sorted(SERVICES)
    for i, (service, rel_words) in enumerate(sorted(SERVICES.items())):
        print service
        cnt = 0
        for word in rel_words:
            print difflib.get_close_matches(word.lower(), words, n=5, cutoff=0.99)
            cnt += len(difflib.get_close_matches(word.lower(), words, n=5, cutoff=0.99))
        print cnt, ""
        if cnt>=1:
            service_flag[i] = 1
    print service_flag
    print ""
    
    print words
    hours_id = None
    if 'hours' in complete_venue:
        print complete_venue['hours'], '\n'
    else:
        print "No hours in venue information\n"
    print ""

    
    rating = None
    if 'rating' in complete_venue:
        print 'rating =', complete_venue['rating'], '\n'
        rating = complete_venue['rating']
        print type(rating)
    else:
        print "No rating in venue information\n"
    print ""
    
    nLikes = None
    if 'likes' in complete_venue:
        print 'likes =', complete_venue['likes']['count'], '\n'
        nLikes = complete_venue['likes']['count']
        print type(nLikes)
    else:
        print "No likes in venue information\n"
        
    print ""
    
    if (len(venue_type)<0):
        venue_type = None
    # phrases 
    # List of phrases commonly seen in this venue's tips, as well as a sample tip snippet and the number of 
    # tips this phrase appears in.
    
    # categories
    # An array, possibly empty, of categories that have been applied to this venue. One of the categories 
    # will have a field primary indicating that it is the primary category for the venue. For the complete 
    # set of categories, see venues/categories. 
    
    # attributes
    # Attributes associated with the venue, such as price tier, whether the venue takes reservations, and 
    # parking availability. 
    
    # tags
    # An array of string tags applied to this venue.
    
    # rating
    # Numerical rating of the venue (0 through 10). Returned as part of an explore result, excluded in 
    # search results. Not all venues will have a rating.
    
    # tips
    # Contains the total count of tips and groups with friends and others as groupTypes. Groups may change 
    # over time. 
    
    # reasons?
    
    # likes 
    # The count of users who have liked this venue, and groups containing any friends and others 
    # who have liked it. The groups included are subject to change. 
    
    # hours
    # Contains the hours during the week that the venue is open along with any named hours segments in a 
    # human-readable format. For machine readable hours see venues/hours
    
