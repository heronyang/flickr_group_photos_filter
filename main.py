#!/usr/bin/python

import json
import urllib2
import os, gc

import csv
import logging

from math import ceil
from IPython.core.debugger import Tracer

# TODO: memory

OUTPUT_FILEPATH = "photos.csv"
LOG_FILEPATH = "main.log"
PER_PAGE_MAX = 500

GroupList = []

logging.basicConfig(filename = LOG_FILEPATH, level = logging.DEBUG)
logger = logging.getLogger()

def getPhotosURLOfGroupBase(groupId, page, per_page):

    apiUrl = "https://api.flickr.com/services/rest/?method=flickr.groups.pools.getPhotos"
    apiKey = "2a2944553ef6c7620d9b4cb932308dd2"
    jsonFormat = "json&nojsoncallback=1"
    extras = "license,owner_name,url_l"

    url = apiUrl \
    + "&api_key=" + apiKey \
    + "&group_id=" + groupId \
    + "&format=" + jsonFormat \
    + "&per_page=" + str(per_page) \
    + "&page=" + str(page) \
    + "&extras=" + extras

    logging.info('api url: ' + url)

    return url

def getPhotosURLOfGroupMinimal(groupId):
    return getPhotosURLOfGroupBase(groupId, 1, 1)

def getPhotosURLOfGroupOnPage(groupId, page):
    return getPhotosURLOfGroupBase(groupId, page, PER_PAGE_MAX)

def getMinPageOfGroupPhotos(groupId):

    url = getPhotosURLOfGroupMinimal(groupId)
    groupPhotos = apiCall(url)

    total = int(groupPhotos['photos']['total'])
    page_n = total / PER_PAGE_MAX
    if (total % PER_PAGE_MAX) != 0:
        page_n += 1

    logging.debug('page_n=' + str(page_n) + " total=" + str(total))
    loggerFlush()

    return page_n

def savePhotosOfGroup(groupId):

    page_n = getMinPageOfGroupPhotos(groupId)

    for p in range(1, page_n+1):
        url = getPhotosURLOfGroupOnPage(groupId, p)
        gp = apiCall(url)
        photos = gp['photos']['photo']
        savePhotos(photos, groupId)
        logging.debug('page ' + str(p) + ' photos saved')
        gc.collect()

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

    logging.debug('save photo: ' + photo['title'] + ', license = ' + photo['license'] + ', owner_name' + photo['owner'])
    to_write = [ groupId, photo['url_l'], photo['license'], photo['owner'] ]
    logging.debug(to_write)
    loggerFlush()

    with open(OUTPUT_FILEPATH, 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"')
        writer.writerow(to_write)

def savePhotos(groupPhotos, groupId):

    count = 0
    for photo in groupPhotos:
        if photo['license'] != '0':
            savePhoto(photo, groupId)
            count += 1

    logging.debug(str(count) + ' photo(s) are saved')

def getPhotosOfAllGroups():
    readGroupListFromFile();
    for group in GroupList:
        groupId = group[1]

        logging.info('Get photo of group: ' + group[0])
        groupPhotos = savePhotosOfGroup(groupId)
        logging.info('Done')

def removePreviousFile():
    try:
        logging.warning('remove previous output file at ' + OUTPUT_FILEPATH)
        os.remove(OUTPUT_FILEPATH)
    except OSError:
        pass

def loggerFlush():
    logger.handlers[0].flush()

def init():
    removePreviousFile()

if __name__ == '__main__':
    logging.debug('start grabbing data...')
    init()
    getPhotosOfAllGroups()

