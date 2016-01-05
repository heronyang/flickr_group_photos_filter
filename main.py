#!/usr/bin/python

import json
import urllib2
import os

import csv

from math import ceil
from IPython.core.debugger import Tracer

OUTPUT_FILEPATH = "photos.csv"

GroupList = []
PhotosOfGroups = {}

PER_PAGE_MAX = 500

def getPhotosURLOfGroupBase(group_id, page, per_page):

    api_url = "https://api.flickr.com/services/rest/?method=flickr.groups.pools.getPhotos"
    api_key = "2a2944553ef6c7620d9b4cb932308dd2"
    json_format = "json&nojsoncallback=1"
    extras = "license,owner_name,url_l"

    url = api_url \
    + "&api_key=" + api_key \
    + "&group_id=" + group_id \
    + "&format=" + json_format \
    + "&per_page=" + str(per_page) \
    + "&page=" + str(page) \
    + "&extras=" + extras

    print 'api url: ' + url

    return url

def getPhotosURLOfGroupMinimal(group_id):
    return getPhotosURLOfGroupBase(group_id, 1, 1)

def getPhotosURLOfGroupOnPage(group_id, page):
    return getPhotosURLOfGroupBase(group_id, page, PER_PAGE_MAX)

def getMinPageOfGroupPhotos(group_id):

    url = getPhotosURLOfGroupMinimal(group_id)
    groupPhotos = apiCall(url)

    total = int(groupPhotos['photos']['total'])
    page_n = total / PER_PAGE_MAX
    if (total % PER_PAGE_MAX) != 0:
        page_n += 1

    print 'page_n=' + str(page_n) + " total=" + str(total)

    return page_n

def getPhotosOfGroup(group_id):

    page_n = getMinPageOfGroupPhotos(group_id)

    result = []
    for p in range(1, page_n+1):
        print 'page ' + str(p)
        url = getPhotosURLOfGroupOnPage(group_id, p)
        gp = apiCall(url)
        result.extend(gp['photos']['photo'])

    print len(result)

    return result

def apiCall(url):
    response = json.load(urllib2.urlopen(url))
    return response

def readGroupListFromFile():
    with open('group_list.csv', 'rb') as csvfile:
        groupList = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in groupList:
            GroupList.append((row[0], row[1]))

def isValidPhoto(photo):
    keys = ('title', 'license', 'owner', 'url_l')
    if all (k in photo for k in keys):
        return True;
    return False

def savePhoto(photo, groupId):

    if not isValidPhoto(photo):
        return

    print 'save photo: ' + photo['title'] + ', license = ' + photo['license'] + ', owner_name' + photo['owner']
    to_write = [ groupId, photo['url_l'], photo['license'], photo['owner'] ]
    print to_write

    with open(OUTPUT_FILEPATH, 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"')
        writer.writerow(to_write)

def savePhotosOfGroup(groupPhotos, groupId):

    count = 0
    for photo in groupPhotos:
        if photo['license'] != '0':
            savePhoto(photo, groupId)
            count += 1

    print str(count) + ' photo(s) are saved'

def getPhotosOfAllGroups():
    readGroupListFromFile();
    for group in GroupList:
        groupId = group[1]

        print 'Get photo of group: ' + group[0]
        groupPhotos = getPhotosOfGroup(groupId)
        print 'Done'

        savePhotosOfGroup(groupPhotos, groupId)

def removePreviousFile():
    try:
        print 'remove previous output file at ' + OUTPUT_FILEPATH
        os.remove(OUTPUT_FILEPATH)
    except OSError:
        pass

def init():
    removePreviousFile()

if __name__ == '__main__':
    init()
    getPhotosOfAllGroups()

