from collections import defaultdict
from Helpers import *
from falcon import uri
import requests
import json
import time
from pprint import pprint

def process(params):
    nested_dict = lambda: defaultdict(nested_dict)
    q = nested_dict()
    q['query']['bool']['filter']['bool']['must'] = []
    q['query']['bool']['filter']['bool']['should'] = []
    q['query']['bool']['must_not'] = []
    params = {k.lower(): v for k, v in params.items()} # Lowercase all parameter names passed
    suggested_sort = "desc";

    conditions = ["subreddit","author"]
    for condition in conditions:
        if condition in params and params[condition] is not None:
            params[condition] = uri.decode(params[condition])
            print (params[condition])
            if not isinstance(params[condition], (list, tuple)):
                params[condition] = params[condition].split(",")
            param_values = [x.lower() for x in params[condition]]
            terms = nested_dict()
            if params[condition][0][0] == "!":
                terms['terms'][condition] = list(map(lambda x:x.replace("!",""),param_values))
                q['query']['bool']['must_not'].append(terms)
            else:
                terms['terms'][condition] = param_values
                q['query']['bool']['filter']['bool']['must'].append(terms)

    if 'delta_only' in params and params['delta_only'] is not None:
        if params['delta_only'].lower() == "true" or params['delta_only'] == "1":
            params['delta_only'] = True

    if 'after' in params and params['after'] is not None:
        if LooksLikeInt(params['after']):
            params['after'] = int(params['after'])
        elif params['after'][-1:].lower() == "d":
            params['after'] = int(time.time()) - (int(params['after'][:-1]) * 86400)
        elif params['after'][-1:].lower() == "h":
            params['after'] = int(time.time()) - (int(params['after'][:-1]) * 3600)
        elif params['after'][-1:].lower() == "m":
            params['after'] = int(time.time()) - (int(params['after'][:-1]) * 60)
        elif params['after'][-1:].lower() == "s":
            params['after'] = int(time.time()) - (int(params['after'][:-1]))
        range = nested_dict()
        range['range']['created_utc']['gt'] = params['after']
        q['query']['bool']['filter']['bool']['must'].append(range)
        suggested_sort = "asc"
    else:
        params['after'] = None

    if 'before' in params and params['before'] is not None:
        if LooksLikeInt(params['before']):
            params['before'] = int(params['before'])
        elif params['before'][-1:].lower() == "d":
            params['before'] = int(time.time()) - (int(params['before'][:-1]) * 86400)
        elif params['before'][-1:].lower() == "h":
            params['before'] = int(time.time()) - (int(params['before'][:-1]) * 3600)
        elif params['before'][-1:].lower() == "m":
            params['before'] = int(time.time()) - (int(params['before'][:-1]) * 60)
        elif params['before'][-1:].lower() == "s":
            params['before'] = int(time.time()) - (int(params['before'][:-1]))
        range = nested_dict()
        range['range']['created_utc']['lt'] = params['before']
        q['query']['bool']['filter']['bool']['must'].append(range)
    else:
        params['before'] = None

    if 'score' in params and params['score'] is not None:
        range = nested_dict()
        if params['score'][:1] == "<":
            range['range']['score']['lt'] = int(params['score'][1:])
        elif params['score'][:1] == ">":
            range['range']['score']['gt'] = int(params['score'][1:])
        elif LooksLikeInt(params['score']):
            range['term']['score'] = int(params['score'])
        q['query']['bool']['filter']['bool']['must'].append(range)

    if 'num_comments' in params and params['num_comments'] is not None:
        range = nested_dict()
        if params['num_comments'][:1] == "<":
            range['range']['num_comments']['lt'] = int(params['num_comments'][1:])
        elif params['num_comments'][:1] == ">":
            range['range']['num_comments']['gt'] = int(params['num_comments'][1:])
        elif LooksLikeInt(params['num_comments']):
            range['term']['num_comments'] = int(params['num_comments'])
        q['query']['bool']['filter']['bool']['must'].append(range)

    conditions = ["over_18","is_video","stickied","spoiler","locked","contest_mode"]
    for condition in conditions:
        if condition in params and params[condition] is not None:
            parameter = nested_dict()
            if params[condition].lower() == 'true' or params[condition] == "1":
                parameter['term'][condition] = "true" 
            elif params[condition].lower() == 'false' or params[condition] == "0":
                parameter['term'][condition] = "false"
            q['query']['bool']['filter']['bool']['must'].append(parameter)

    if 'sort_type' in params and params['sort_type'] is not None:
        params["sort_type"] = params['sort_type'].lower()
    else:
        params["sort_type"] = "created_utc"

    if 'limit' in params:
        params['size'] = params['limit']

    if 'size' in params and params['size'] is not None and LooksLikeInt(params['size']):
        size = 500 if int(params['size']) > 500 else int(params['size'])
        q['size'] = params['size'] = size
    else:
        q['size'] = params['size'] = 25

    if 'order' in params and params['order'] is not None:
        params['sort'] = params['order'].lower()

    if 'sort' in params and params['sort'] is not None:
        params['sort'] = params['sort'].lower()
        if params['sort'] != "asc" and params['sort'] != "desc":
            params['sort'] = suggested_sort
    else:
        params['sort'] = suggested_sort
    q['sort'][params['sort_type']] = params['sort']

    if 'frequency' in params and params['frequency'] is not None:
        if params['frequency'][-1:] in ['s','m','h','d','w','M','y'] and LooksLikeInt(params['frequency'][:1]):
            time_unit = params['frequency'][-1:]
            time_period = {'s':'second','m':'minute','h':'hour','d':'day','w':'week','M':'month','y':'year'}
            length = params['frequency'][:-1]
            params['frequency'] = str(length) + time_unit
        elif 'frequency' in params and params['frequency'].lower() in ['second','minute','hour','day','week','month','year']:
            params['frequency'] = params['frequency'].lower()
        else:
            params['frequency'] = None
    return(params,q)

