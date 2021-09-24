from haystackapp.apps import hspipe
import json

def search(query, debug=False):
    if debug:
        result = ''
        result += 'Query: ' + query + '\n'
        result += 'Answer: I don\'t know jack shit!'
        if 'test' in hspipe:
            result += '\nHaystack pipeline is accessible. YES!'
        return result

    # You can configure how many candidates the reader and retriever shall return
    # The higher top_k_retriever, the better (but also the slower) your answers. 
    # results = pipe.run(query=query, top_k_retriever=10, top_k_reader=5)
    results = hspipe.run(query=query, top_k_retriever=10)

    # remove unwanted attributes (may depend on search method)
    # for result in results:
    #     result.pop('question')
    #     result.pop('embedding')

    # remove titles from text
    for result in results['documents']:
        text = result['text']
        i = 0
        close_bracks_seen = 0
        while i < len(text) - 1 and close_bracks_seen < 2:
            if text[i] == ']':
                close_bracks_seen += 1
            i += 1
        i += 1
        text = text[i:]
        result['text'] = text

    # print(type(results))
    return results