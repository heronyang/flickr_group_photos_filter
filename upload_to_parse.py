#!/usr/bin/python

import csv
import sys
import logging
import json, httplib

import ConfigParser

from IPython.core.debugger import Tracer

INPUT_PHOTO_FILE = "photos_sub.csv"
INPUT_GROUP_FILE = "group_list_sub.csv"
CONFIG_FILE = "config.cfg"

PARSE_APPLICATION_ID = ""
PARSE_REST_API_KEY = ""

GroupList = []
PhotoList = []

MapGroupNameToParseId = {}

def readParseConfig():

    global PARSE_APPLICATION_ID, PARSE_REST_API_KEY
    config = ConfigParser.ConfigParser()

    try:
        config.read(CONFIG_FILE)

        PARSE_APPLICATION_ID = config.get('Parse', 'application-id')
        PARSE_REST_API_KEY = config.get('Parse', 'rest-api-key')

    except ConfigParser.Error:
        print 'Config Parser Error'
        sys.stdout.flush()
        exit()

    print PARSE_APPLICATION_ID, PARSE_REST_API_KEY
    sys.stdout.flush()

class Group:

    def __init__(self, name, id):
        self.name = name
        self.id = id

    def __str__(self):
        return "[Group] " + self.name + "(" + self.id + ")"

class Photo:

    def __init__(self, group, url, permission, ownerId):
        self.group = group
        self.url = url
        self.permission = permission
        self.ownerId = ownerId

    def __str__(self):
        return "[Photo] " + self.url + "(" + self.permission + ")"

def getGroupFromListById(groupId):

    for group in GroupList:
        if group.id == groupId:
            return group

    raise KeyError('Wrong Group ID')

def readPhotoDataFromCSV():

    with open(INPUT_PHOTO_FILE, 'rb') as csvfile:

        photoList = csv.reader(csvfile, delimiter=',', quotechar='"')

        for photoData in photoList:

            group = getGroupFromListById(photoData[0])
            url = photoData[1]
            permission = int(photoData[2])
            ownerId = photoData[3]

            photo = Photo(group, url, permission, ownerId)
            PhotoList.append(photo)

def readGroupDataFromCSV():

    with open(INPUT_GROUP_FILE, 'rb') as csvfile:

        groupList = csv.reader(csvfile, delimiter=',', quotechar='"')

        for row in groupList:
            groupName = row[0]
            groupId = row[1]
            group = Group(groupName, groupId)
            GroupList.append(group)

def commitPhotosToParse():
    for photo in PhotoList:
        photoParseId = commitOnePhotoToParse(photo)
        updateGroupPointer(photo, photoParseId)

def commitOnePhotoToParse(photo):

    connection = httplib.HTTPSConnection('api.parse.com', 443)
    connection.connect()
    connection.request('POST', '/1/classes/FlickrPhotoOfGroups', json.dumps({
        "url": photo.url,
        "permission": photo.permission,
        "ownerFlickrId": photo.ownerId
        }), {
            "X-Parse-Application-Id": PARSE_APPLICATION_ID,
            "X-Parse-REST-API-Key": PARSE_REST_API_KEY,
            "Content-Type": "application/json"
            })
    results = json.loads(connection.getresponse().read())
    print results
    sys.stdout.flush()

    connection.close()
    return results['objectId']

def updateGroupPointer(photo, photoParseId):

    groupParseId = MapGroupNameToParseId[photo.group.name]

    connection = httplib.HTTPSConnection('api.parse.com', 443)
    connection.connect()
    connection.request('PUT', '/1/classes/FlickrGroup/' + groupParseId, json.dumps({
    "photos": {
        "__op": "AddRelation",
        "objects": [{
            "__type": "Pointer",
            "className": "FlickrPhotoOfGroups",
            "objectId": photoParseId
            }]
        }
    }), {
        "X-Parse-Application-Id": PARSE_APPLICATION_ID,
        "X-Parse-REST-API-Key": PARSE_REST_API_KEY,
        "Content-Type": "application/json"
        })
    result = json.loads(connection.getresponse().read())
    print result
    sys.stdout.flush()

    connection.close()


def commitGroupsToParse():
    for group in GroupList:
        commitOneGroupToParse(group)

def commitOneGroupToParse(group):

    connection = httplib.HTTPSConnection('api.parse.com', 443)
    connection.connect()
    connection.request('POST', '/1/classes/FlickrGroup', json.dumps({
        "name": group.name,
        "flickrId": group.id
        }), {
            "X-Parse-Application-Id": PARSE_APPLICATION_ID,
            "X-Parse-REST-API-Key": PARSE_REST_API_KEY,
            "Content-Type": "application/json"
            })
    results = json.loads(connection.getresponse().read())
    saveParseResult(group, results)
    print results
    sys.stdout.flush()

    connection.close()

def saveParseResult(group, results):
    MapGroupNameToParseId[group.name] = results['objectId']

if __name__ == '__main__':

    readParseConfig()

    readGroupDataFromCSV()
    commitGroupsToParse()

    readPhotoDataFromCSV()
    commitPhotosToParse()
