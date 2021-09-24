from json.decoder import JSONDecodeError
from django.shortcuts import render
from django.http import HttpResponse

import requests
import json

from haystackapp.src.haystackpipline import search

# Create your views here.
def index(request):
    if 'q' not in request.GET:
        # no search query was provided
        return HttpResponse("Welcome to YTHP. Please provide a search query.")

    query = request.GET['q']
    # search query was provided, so let's ask for an answer from our Haystack pipeline
    results = search(query)

    # Reformat results so that excerpts from the same document are grouped together
    formatted_results = []
    vids_seen = set()
    for doc in results['documents']:
        vid = doc['meta']['name'][:-4] # remove '.txt'
        if vid not in vids_seen:
            # fetch video title from YouTube
            title = '?'
            channel = '?'
            r = requests.get(f'https://youtube.com/oembed?url=https://youtu.be/{vid}&format=json')
            try:
                j = r.json()
                title = j['title']
                channel = j['author_name']
            except JSONDecodeError as e:
                print('Failed request for video w/ ID ' + vid)

            result = {
                "vid" : vid,
                "title" : title,
                "channel" : channel,
                "excerpts" : [ 
                    {
                        "text" : doc['text'],
                        "timestamp" : "1:23:45" # TODO: replace with actual timestamp
                    }
                ]
            }
            formatted_results.append(result)
            vids_seen.add(vid)
        else:
            # find existing result and add this excerpt to it
            for result in formatted_results:
                if result['vid'] == vid:
                    result['excerpts'].append({
                        "text" : doc['text'],
                        "timestamp" : "1:23:45" # TODO: replace with actual timestamp
                    })
                    break

    return HttpResponse(json.dumps(formatted_results))
