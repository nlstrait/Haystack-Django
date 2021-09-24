"""
Classes and functions for interfacing with YouTube via their official API and through youtube-dl, 
the open-source project.
"""

from json.decoder import JSONDecodeError
import requests


"""
Fetch a list of video metadata (titles and channel names) which map to a given list of video IDs.
Returns dictionary mapping video IDs to metadata.
"""
def fetch_metadata(video_ids):
    ids_to_titles = {}
    for id in video_ids:
        r = requests.get(f'https://youtube.com/oembed?url=https://youtu.be/{id}&format=json')
        try:
            j = r.json()
            title = j['title']
            channel_name = j['author_name']
            ids_to_titles[id] = title + ' | ' + channel_name
        except JSONDecodeError as e:
            print('Failed request for video ' + id)
    return ids_to_titles


# Testing

def test():
    video_ids = [
        'RfocDdUn9tI',
        'HitOU27liRY'
    ]
    metadata = fetch_metadata(video_ids)
    print(metadata)


if '__name__' == '__main__':
    test()