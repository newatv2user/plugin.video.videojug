import urllib, urllib2, re, sys, cookielib, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from xbmcgui import ListItem
import CommonFunctions
import StorageServer

# plugin constants
### get addon info
Addon = xbmcaddon.Addon()
AddonId = Addon.getAddonInfo('id')
PluginHandle = int(sys.argv[1])

rootDir = Addon.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = xbmc.translatePath(rootDir)

# For parsedom
common = CommonFunctions
common.dbg = False
common.dbglevel = 3

# initialise cache object to speed up plugin operation
cache = StorageServer.StorageServer(AddonId)

search_thumb = os.path.join(rootDir, 'resources', 'media', 'search.png')
next_thumb = os.path.join(rootDir, 'resources', 'media', 'next.png')
shows_thumb = os.path.join(rootDir, 'resources', 'media', 'shows.png')

########################################################
## URLs
########################################################
BASE_URL = 'http://www.videojug.com'

########################################################
## Modes
########################################################
M_DO_NOTHING = 0
M_BROWSE = 10
M_PLAY = 40
M_SEARCH = 60

##################
## Class for items
##################
class MediaItem:
    def __init__(self):
        self.ListItem = ListItem()
        self.Image = ''
        self.Url = ''
        self.Isfolder = False
        self.Mode = ''
        
## Get URL
def getURL(url):
    print 'getURL :: url = ' + url
    cj = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2;)')]
    response = opener.open(url)
    html = response.read()
    ret = {}
    ret['html'] = html 
    return ret

def cleanHtml(dirty):
    # Remove HTML codes
    clean = re.sub('&quot;', '\"', dirty)
    clean = re.sub('&#039;', '\'', clean)
    clean = re.sub('&#215;', 'x', clean)
    clean = re.sub('&#038;', '&', clean)
    clean = re.sub('&#8216;', '\'', clean)
    clean = re.sub('&#8217;', '\'', clean)
    clean = re.sub('&#8211;', '-', clean)
    clean = re.sub('&#8220;', '\"', clean)
    clean = re.sub('&#8221;', '\"', clean)
    clean = re.sub('&#8212;', '-', clean)
    clean = re.sub('&amp;', '&', clean)
    clean = re.sub("`", '', clean)
    clean = re.sub('<em>', '[I]', clean)
    clean = re.sub('</em>', '[/I]', clean)
    clean = re.sub('<strong>', '', clean)
    clean = re.sub('</strong>', '', clean)
    clean = re.sub('<br />', '\n', clean)
    return clean

def BuildMainDirectory():
    ########################################################
    ## Mode = None
    ## Build the main directory
    ########################################################
    
    data = cache.cacheFunction(getURL, BASE_URL + '/categories')
    if not data:
        return
    data = data['html']
    all_channels_menu = common.parseDOM(data, "nav", {"id": "all_channels_menu"})[0]
    Items = common.parseDOM(all_channels_menu, "li")
    if not Items:
        return
    
    MediaItems = []
    for item in Items:        
        Mediaitem = MediaItem()
        Mediaitem.Image = shows_thumb
        Mediaitem.Mode = M_BROWSE
        
        Url = common.parseDOM(item, "a", ret="href")
        if not Url:
            continue
        Url = Url[0]
        Title = common.parseDOM(item, "span", {"class": "text"})
        if not Title:
            continue
        Title = Title[0]
        Title = common.replaceHTMLCodes(Title)      
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.quote_plus(BASE_URL + Url) + "&mode=" \
                        + str(Mediaitem.Mode) + "&name=" + urllib.quote_plus(Title)
        Mediaitem.ListItem.setInfo('video', { 'Title': Title})
        Mediaitem.ListItem.setThumbnailImage(Mediaitem.Image)
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.Isfolder = True
        MediaItems.append(Mediaitem)
    # Add more menu items for browsing
    Menu = [('Search', '', search_thumb, M_SEARCH)]
    for Title, URL, Thumb, Mode in Menu:
        Mediaitem = MediaItem()
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.quote_plus(URL) + "&mode=" + str(Mode) + "&name=" + urllib.quote_plus(Title)
        Mediaitem.ListItem.setThumbnailImage(Thumb)
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.Isfolder = True
        MediaItems.append(Mediaitem)
        
    addDir(MediaItems)

    # End of Directory
    xbmcplugin.endOfDirectory(PluginHandle)
    
# Probably need to do different ones for TV shows
def Browse(Url):
    # set content type so library shows more views and info
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    data = cache.cacheFunction(getURL, Url)
    if not data:
        return
    data = data['html']
    video_wall_items = common.parseDOM(data, "ul", {"id": "video_wall_items"})[0]
    Items = common.parseDOM(video_wall_items, "li", {"role": "listitem"})
    if not Items:
        return
    
    MediaItems = []
    for Item in Items:
        Duration = common.parseDOM(Item, "span", {"class": "duration"})
        if not Duration:
            Duration = ''
        else:
            Duration = Duration[0]
            
        Href = common.parseDOM(Item, "a", ret="href")
        if not Href:
            continue
        Href = Href[0]
            
        Image = common.parseDOM(Item, "img", ret="data-src")
        if not Image:
            Image = ''
        else:
            Image = Image[0]
        #print Image    
        Title = common.parseDOM(Item, "strong")
        if not Title:
            continue
        Title = Title[0]
        Title = common.replaceHTMLCodes(Title)
        Title = Title.encode('utf-8')
                
        Plot = common.parseDOM(Item, "img", ret="alt")
        if not Plot:
            Plot = ''
        else:
            Plot = Plot[0]
            Plot = common.replaceHTMLCodes(Plot)
            
        Genres = common.parseDOM(Item, "a", {"class": "botNoFollow"})
        Genre = ''
        if not Genres:
            Genre = ''
        else:
            Genre = Genres[0]
            Genre = common.replaceHTMLCodes(Genre)
        
        Mediaitem = MediaItem()
        Mediaitem.Image = Image
        Mediaitem.Mode = M_PLAY
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.quote_plus(BASE_URL + Href) + "&mode=" + str(Mediaitem.Mode) + "&name=" + urllib.quote_plus(Title)
        Mediaitem.ListItem.setInfo('video', { 'Title': Title, 'Plot': Plot, 'Genre': Genre,
                                             'Duration': Duration})
        Mediaitem.ListItem.setThumbnailImage(Mediaitem.Image)
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.ListItem.setProperty('IsPlayable', 'true')
        MediaItems.append(Mediaitem)
    
    # Next Page:
    pagination = common.parseDOM(data, "a", {"id": "pagination_next"}, ret="href")
    if pagination:
        Mediaitem = MediaItem()
        Title = "Next"
        Url = BASE_URL + pagination[0]
        Mediaitem.Image = next_thumb
        Mediaitem.Mode = M_BROWSE
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.quote_plus(Url) + "&mode=" + str(Mediaitem.Mode) + "&name=" + urllib.quote_plus(Title)
        Mediaitem.ListItem.setInfo('video', { 'Title': Title})
        Mediaitem.ListItem.setThumbnailImage(Mediaitem.Image)
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.Isfolder = True
        MediaItems.append(Mediaitem)
    
    # Add more menu items for browsing
    Menu = [('Search', '', search_thumb, M_SEARCH)]
    for Title, URL, Thumb, Mode in Menu:
        Mediaitem = MediaItem()
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.quote_plus(URL) + "&mode=" + str(Mode) + "&name=" + urllib.quote_plus(Title)
        Mediaitem.ListItem.setThumbnailImage(Thumb)
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.Isfolder = True
        MediaItems.append(Mediaitem)
    
    if MediaItems:        
        addDir(MediaItems)
    
    # End of Directory
    xbmcplugin.endOfDirectory(PluginHandle)
    ## Set Default View Mode. This might break with different skins. But who cares?
    SetViewMode()
    
def Search(Url):
    if Url == '':
        keyb = xbmc.Keyboard('', 'Search Vidics.eu')
        keyb.doModal()
        if (keyb.isConfirmed() == False):
            return
        search = keyb.getText()
        if not search or search == '':
            return
    
        search = search.replace(' ', '+')
        Url = BASE_URL + '/search?keywords=%s' % search
    # set content type so library shows more views and info
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    data = cache.cacheFunction(getURL, Url)
    if not data:
        return
    data = data['html']
    Items = common.parseDOM(data, "div", {"class": "search-result search-result-content"})
    if not Items:
        return
    
    MediaItems = []
    for Item in Items:
        Duration = common.parseDOM(Item, "span", {"class": "duration"})
        if not Duration:
            Duration = ''
        else:
            Duration = Duration[0]
            
        Href = common.parseDOM(Item, "a", ret="href")
        if not Href:
            continue
        Href = Href[0]
            
        Image = common.parseDOM(Item, "img", ret="data-src")
        if not Image:
            Image = ''
        else:
            Image = Image[0]
        #print Image    
        Title = common.parseDOM(Item, "h2")
        if not Title:
            continue
        Title = Title[0]
        Title = common.stripTags(Title)
        Title = common.replaceHTMLCodes(Title)
        Title = Title.encode('utf-8')
                
        Plot = common.parseDOM(Item, "p")
        if not Plot:
            Plot = ''
        else:
            Plot = Plot[0]
            Plot = common.replaceHTMLCodes(Plot)
            Plot = common.stripTags(Plot)
            
        Mediaitem = MediaItem()
        Mediaitem.Image = Image
        Mediaitem.Mode = M_PLAY
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.quote_plus(BASE_URL + Href) + "&mode=" + str(Mediaitem.Mode) + "&name=" + urllib.quote_plus(Title)
        Mediaitem.ListItem.setInfo('video', { 'Title': Title, 'Plot': Plot, 'Duration': Duration})
        Mediaitem.ListItem.setThumbnailImage(Mediaitem.Image)
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.ListItem.setProperty('IsPlayable', 'true')
        MediaItems.append(Mediaitem)
        
    # Next Page:
    search_result_summary = common.parseDOM(data, "div", {"id": "search_result_summary"})
    if search_result_summary:
        search_result_summary = search_result_summary[0]
        Total = re.compile('Total Results: (\d+)').findall(search_result_summary)
        if Total:
            Total = int(Total[0])
            Page = re.compile('page=(\d+)').findall(Url)
            if Page:
                Page = int(Page[0])
            else:
                Page = 0
            if Page * 10 < Total:
                Mediaitem = MediaItem()
                Title = "Next"
                if Page == 0:
                    nurl = Url
                    Npage = 2
                else:
                    nurl = Url.split('&')[0]
                    Npage = Page + 1
                Url = nurl + '&page=%d&content=All&sort=Relevance' % Npage
                Mediaitem.Image = next_thumb
                Mediaitem.Mode = M_SEARCH
                Mediaitem.Url = sys.argv[0] + "?url=" + urllib.quote_plus(Url) + "&mode=" + str(Mediaitem.Mode) + "&name=" + urllib.quote_plus(Title)
                Mediaitem.ListItem.setInfo('video', { 'Title': Title})
                Mediaitem.ListItem.setThumbnailImage(Mediaitem.Image)
                Mediaitem.ListItem.setLabel(Title)
                Mediaitem.Isfolder = True
                MediaItems.append(Mediaitem)
    
    if MediaItems:        
        addDir(MediaItems)
    
    # End of Directory
    xbmcplugin.endOfDirectory(PluginHandle)
    ## Set Default View Mode. This might break with different skins. But who cares?
    SetViewMode()

def Play(Url):
    ###########################################################
    ## Mode == M_PLAY
    ## Try to get a list of playable items and play it.
    ###########################################################
    data = cache.cacheFunction(getURL, Url)
    if not data:
        dialog = xbmcgui.Dialog()
        dialog.ok('Error', 'Error getting webpage.')
        xbmcplugin.setResolvedUrl(PluginHandle, False, xbmcgui.ListItem())
        return
    data = data['html']
    contentid = common.parseDOM(data, "body", ret="data-contentid")
    if not contentid:
        return
    contentid = contentid[0]
    pUrl = 'http://www.videojug.com/feed/playlist?id=%s&items=&userName=&ar=16_9' % contentid
    pdata = cache.cacheFunction(getURL, pUrl)
    if not pdata:
        dialog = xbmcgui.Dialog()
        dialog.ok('Error', 'Error getting webpage.')
        xbmcplugin.setResolvedUrl(PluginHandle, False, xbmcgui.ListItem())
        return
    pdata = pdata['html']
    Movie_Link = common.parseDOM(pdata, "Location", {"Name": "content3.videojug.com"},
                                 ret="Url")
    if not Movie_Link:
        dialog = xbmcgui.Dialog()
        dialog.ok('Error', 'No Links Found.')
        xbmcplugin.setResolvedUrl(PluginHandle, False, xbmcgui.ListItem())
        return
    Movie_Link = Movie_Link[0]
    Prefix = common.parseDOM(pdata, "Media", {"Type": "Video"}, ret="Prefix")[0]
    URL = Movie_Link + Prefix + '__VJ480PENG.mp4?px-bps=1400000&px-bufahead=4'
    xbmcplugin.setResolvedUrl(PluginHandle, True, xbmcgui.ListItem(path=URL))
    
# Set View Mode selected in the setting
def SetViewMode():
    try:
        # if (xbmc.getSkinDir() == "skin.confluence"):
        if Addon.getSetting('view_mode') == "1": # List
            xbmc.executebuiltin('Container.SetViewMode(502)')
        if Addon.getSetting('view_mode') == "2": # Big List
            xbmc.executebuiltin('Container.SetViewMode(51)')
        if Addon.getSetting('view_mode') == "3": # Thumbnails
            xbmc.executebuiltin('Container.SetViewMode(500)')
        if Addon.getSetting('view_mode') == "4": # Poster Wrap
            xbmc.executebuiltin('Container.SetViewMode(501)')
        if Addon.getSetting('view_mode') == "5": # Fanart
            xbmc.executebuiltin('Container.SetViewMode(508)')
        if Addon.getSetting('view_mode') == "6":  # Media info
            xbmc.executebuiltin('Container.SetViewMode(504)')
        if Addon.getSetting('view_mode') == "7": # Media info 2
            xbmc.executebuiltin('Container.SetViewMode(503)')
            
        if Addon.getSetting('view_mode') == "0": # Media info for Quartz?
            xbmc.executebuiltin('Container.SetViewMode(52)')
    except:
        print "SetViewMode Failed: " + Addon.getSetting('view_mode')
        print "Skin: " + xbmc.getSkinDir()


## Get Parameters
def get_params():
        param = []
        paramstring = sys.argv[2]
        if len(paramstring) >= 2:
                params = sys.argv[2]
                cleanedparams = params.replace('?', '')
                if (params[len(params) - 1] == '/'):
                        params = params[0:len(params) - 2]
                pairsofparams = cleanedparams.split('&')
                param = {}
                for i in range(len(pairsofparams)):
                        splitparams = {}
                        splitparams = pairsofparams[i].split('=')
                        if (len(splitparams)) == 2:
                                param[splitparams[0]] = splitparams[1]
        return param

def addDir(Listitems):
    if Listitems is None:
        return
    Items = []
    for Listitem in Listitems:
        Item = Listitem.Url, Listitem.ListItem, Listitem.Isfolder
        Items.append(Item)
    handle = PluginHandle
    xbmcplugin.addDirectoryItems(handle, Items)


'''if not os.path.exists(settingsDir):
    os.mkdir(settingsDir)
if not os.path.exists(cacheDir):
    os.mkdir(cacheDir)'''
                    
params = get_params()
url = None
name = None
mode = None

try:
        url = urllib.unquote_plus(params["url"])
except:
        pass
try:
        name = urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode = int(params["mode"])
except:
        pass

xbmc.log("Mode: " + str(mode))
#print "URL: " + str(url)
#print "Name: " + str(name)

if mode == None:
    BuildMainDirectory()
elif mode == M_DO_NOTHING:
    print 'Doing Nothing'
elif mode == M_BROWSE:
    Browse(url)
elif mode == M_PLAY:
    Play(url)
elif mode == M_SEARCH:
    Search(url)
