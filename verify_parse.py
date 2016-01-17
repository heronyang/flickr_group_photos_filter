#!/usr/bin/python

import csv
import logging
import json, httplib

import ConfigParser

from IPython.core.debugger import Tracer

INPUT_GROUP_FILE = "group_list.csv"
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
        exit()

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

def readGroupDataFromCSV():

    with open(INPUT_GROUP_FILE, 'rb') as csvfile:

        groupList = csv.reader(csvfile, delimiter=',', quotechar='"')

        for row in groupList:
            groupName = row[0]
            groupId = row[1]
            group = Group(groupName, groupId)
            GroupList.append(group)

def getAmountGroupPhotoAmountFromParseApi():

    connection = httplib.HTTPSConnection('api.parse.com', 443)
    connection.connect()

    for group in GroupList:

        flickrId = group.id

        connection.request('POST', '/1/functions/getAmountOfGroup', json.dumps({
            "flickrId": flickrId
            }), {
                "X-Parse-Application-Id": PARSE_APPLICATION_ID,
                "X-Parse-REST-API-Key": PARSE_REST_API_KEY,
                "Content-Type": "application/json"
                })
        results = json.loads(connection.getresponse().read())
        amount = results['result']

        print group.name, ":", amount

    connection.close()

if __name__ == '__main__':

    readParseConfig()
    readGroupDataFromCSV()

    getAmountGroupPhotoAmountFromParseApi();

