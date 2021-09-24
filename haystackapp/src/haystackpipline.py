from haystackapp.apps import hspipe

def search(query):
    result = ''
    result += 'Query: ' + query + '\n'
    result += 'Answer: I don\'t know anything!'
    if 'test' in hspipe:
        result += '\nHaystack pipeline is accessible.'
    return result
