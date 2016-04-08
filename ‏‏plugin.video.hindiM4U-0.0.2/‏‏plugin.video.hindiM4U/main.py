# Author: ClownCrown
# Created on: 02.04.2016
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
import urllib
import urlparse
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import requests
from bs4 import BeautifulSoup
import unicodedata

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

CatsWithHrefs = {}
catagories = []

def addDir(name,url,mode,iconimage,PageNumber):
    u=sys.argv[0]+"?url="+ url +"&action="+str(mode)+"&name="+name+"&page="+str(PageNumber)
    liz=xbmcgui.ListItem(unicode(name), iconImage="DefaultFolder.png",thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, 'year':"" })
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

def get_categories():
    """
    Get the list of video categories.
    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.
    :return: list
    """
    gPageNumber = 1
    siteReq = requests.get("http://www.hindilinks4u.to/")
    siteSoup = BeautifulSoup(siteReq.content, "html.parser")
    cats = (siteSoup.find("div", class_="widget widget_categories"))
    for catslink in cats.find_all("li"):
        link = catslink.contents[0].get("href")
        catagories.append([link[link.rfind("/")+1:], link])
        #CatsWithHrefs[catslink.contents[0].text] = catslink.contents[0].get("href")
    #print CatsWithHrefs.keys()
    siteReq.close()
    return catagories

def get_links(html,page):
    linksList = []
    if page != 0:
        html = html + "/page/" + str(page)
    print "Starting to load movies from"
    print html
    try:
        r = requests.get(html)
        if(r.status_code == 200):
            soup = BeautifulSoup(r.content, "html.parser")
            pageLink = soup.find("a",class_="nextpostslink").attrs["href"][soup.find("a",class_="nextpostslink").attrs["href"].rfind("/")+1:]
            for link in soup.find_all("a", class_="clip-link"):
                if link.get("title").find("In Hindi") == -1:
                    titleLink = link.get("title")
                    refLink = link.get("href")
                    imgLink = link.contents[1].contents[1].attrs['src']
                    moviedic = {'name': titleLink, 'ref': refLink, 'thumb': imgLink, 'video': "", 'reldate': "",'syn': "", 'page': pageLink}

                    #for every link, get movie link from the site
                    htm = moviedic["ref"]
                    rlink = requests.get(htm)
                    souplink = BeautifulSoup(rlink.content, "html.parser")
                    movieLink = souplink.iframe['src']
                    movieCon = requests.get(movieLink)
                    soupMov = BeautifulSoup(movieCon.content, "html.parser")
                    try:
                        moviedic["video"] = soupMov.video.source["src"]
                        # print moviedic["name"]
                        # get movie's release date and synopses
                        # -- --
                        # temp = (souplink.find("div",class_="entry-content rich-content").contents[9].text).split(" ")
                        # temp.reverse()
                        # moviedic["reldate"] = temp[0]
                        index = moviedic["name"].rfind('(')
                        temp = moviedic["name"][index+1:moviedic["name"].__len__()-1]
                        moviedic["reldate"] = temp
                        for con in souplink.find("div",class_="entry-content rich-content").contents:
                            if not(isinstance(con, basestring)):
                                if (con.text.find("Synopsis") != -1):
                                    moviedic["syn"] = con.text.split(":")[1]
                                    break
                        linksList.append(moviedic)
                    except AttributeError:
                        moviedic["name"] = moviedic["name"] + " dead link"
                        print moviedic["name"]
                    rlink.close()
            r.close()
    except requests.ConnectionError, requests.HTTPError:
        # to return empty list
        moviedic = {'name': "", 'ref': "", 'thumb': "", 'video': "", 'reldate': "",'syn': "", 'page': ""}
        linksList.append(moviedic)
    return linksList

def get_videos(category,page):
    """
    Get the list of videofiles/streams.
    Here you can insert some parsing code that retrieves
    the list of videostreams in a given category from some site or server.
    :param category: str
    :return: list
    """
    categories = get_categories()
    print "catagory to load: " + str(category)
    print "catagories: "
    print catagories
    for cat in catagories:
        print category , cat
        if(cat[0].lower() == category.lower()):
            html = cat[1]
            print "found"
            break
    if page != 0:
        print "take links  from the next page"
        return get_links(html, page)
    else:
        return get_links(html, page)



def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Get video categories
    categories = get_categories()
    print "catagories to itemlist: "
    print catagories
    # Create a list for our items.
    listing = []
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category[0])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        # list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
        #                  'icon': VIDEOS[category][0]['thumb'],
        #                  'fanart': VIDEOS[category][0]['thumb']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': category[0], 'genre': category[0]})
        # Create a URL for the plugin recursive callback.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = '{0}?action=listing&category={1}'.format(_url, category[0])
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by ove via addDirectoryItem.
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_videos(category,page):
    """
    Create the list of playable videos in the Kodi interface.
    :param category: str
    """
    # Get the list of videos in the category.
    if page == 0:
        videos = get_videos(category, 0)
    else:
        print "move to the next page"
        videos = get_videos(category, page)
    # Create a list for our items.
    listing = []
    # Iterate through videos.
    page = videos[0]['page']
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        list_item.setInfo('video', {'title': video['name'], 'genre': category, 'year': video['reldate'], 'plotoutline': video['syn'],'plot': video['syn']})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for the plugin recursive callback.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/vids/crab.mp4
        url = '{0}?action=play&video={1}'.format(_url, video['video']).decode('utf-8')
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by ove via addDirectoryItem.
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.setContent(_handle, 'movies')
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE_TAKEN)
    xbmcplugin.addSortMethod(handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE)
    catagories = get_categories()
    for cat in catagories:
        if(cat[0].lower() == category.lower()):
            foundCat = cat[1]
            break

    addDir(">>_next-page_>>",foundCat,1,"",page)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play_video(path):
    """
    Play a video by the provided path.
    :param path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path.decode('utf-8'))
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    print params
    if params:
        if params['action'] == str(1):
            # load more links
            catagory = params['url'][params['url'].rfind("/")+1:]
            print "load another list"
            list_videos(catagory,params['page'])
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['category'], 0)
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
