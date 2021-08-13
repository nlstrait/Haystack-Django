from django.shortcuts import render
from django.http import HttpResponse

from haystackapp.src.haystackpipline import search

# Create your views here.
def index(request):
    if 'q' not in request.GET:
        # no search query was provided
        return HttpResponse("Welcome to YTHP. Please provide a search query.")
    else:
        query = request.GET['q']
        # search query was provided, so let's ask for an answer from our Haystack pipeline
        result = search(query)
        return HttpResponse(result)
