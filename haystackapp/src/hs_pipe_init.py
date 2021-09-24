"""
Ported from this Jupyter Notebook on learning Haystack: https://colab.research.google.com/drive/1byg3cEEDUnHUpllP_lsnDIJamjSTzc3C?usp=sharing
"""

from haystack import document_store
from haystack.preprocessor.preprocessor import PreProcessor
# from haystack.preprocessor.cleaning import clean_wiki_text
from haystack.preprocessor.utils import convert_files_to_dicts, fetch_archive_from_http
from haystack.reader.farm import FARMReader
from haystack.reader.transformers import TransformersReader
# from haystack.utils import print_answers

import os
from sys import platform
import time
import re

from haystackapp.src.youtube_interface import fetch_metadata


def initialize(verbose=True, debug=False):
    pipe = construct_simple_pipeline(verbose=verbose)
    # pipe = construct_advanced_pipeline(verbose=verbose)

    if debug:
        return {'test':'yes'}
    else:
        return pipe


"""
Constructs an advanced Haystack pipeline using FAISS and a Dense Passage Retriever.

This pipeline is computationally expensive (best w/ GPU) and takes time to initialize but allows title embedding and gives better results.
Constructed following this tutorial: https://haystack.deepset.ai/docs/latest/tutorial6md
"""
def construct_advanced_pipeline(verbose=True):
    # Initialize FAISS document store
    from haystack.document_store import FAISSDocumentStore
    document_store = FAISSDocumentStore(faiss_index_factory_str="Flat")
    preprocess_documents(document_store) # may be doing too much preprocessing for dense retrieval

    # Initialize Retriever (and Reader and/or Finder)
    from haystack.retriever.dense import DensePassageRetriever
    retriever = DensePassageRetriever(document_store=document_store,
                          query_embedding_model="facebook/dpr-question_encoder-single-nq-base",
                          passage_embedding_model="facebook/dpr-ctx_encoder-single-nq-base",
                          embed_title=True,
                          use_fast_tokenizers=True # not sure what this does...
                        )
    document_store.update_embeddings(retriever)

    # Construct pipeline
    from haystack.pipeline import DocumentSearchPipeline, SearchSummarizationPipeline
    pipe = DocumentSearchPipeline(retriever)
    return pipe


"""
Constructs a simple Haystack pipeline using Elasticsearch and a basic retriever.

This pipeline is less computationally expensive (does not need GPU) and initializes quickly but is relatively inaccurate/unhelpful.
"""
def construct_simple_pipeline(verbose=True):
    # Initialize Elasticsearch document store
    start_elasticsearch(verbose=verbose)
    from haystack.document_store.elasticsearch import ElasticsearchDocumentStore
    document_store = ElasticsearchDocumentStore(host="localhost", username="", password="", index="document")
    preprocess_documents(document_store)

    # Initialize Retriever
    from haystack.retriever.sparse import ElasticsearchRetriever
    retriever = ElasticsearchRetriever(document_store=document_store)

    # Construct pipeline
    from haystack.pipeline import DocumentSearchPipeline
    pipe = DocumentSearchPipeline(retriever)
    return pipe


def start_elasticsearch(verbose=True):
    # Recommended: Start Elasticsearch using Docker via the Haystack utility function
    # from haystack.utils import launch_es
    # launch_es()

    # Start Elasticsearch from source
    es_version = '7.14.0'
    if not os.path.isdir('elasticsearch-' + es_version):
        if verbose:
            print('Installing Elasticsearch...')
        # Install Elasticsearch
        if platform == 'linux' or platform == 'linux2':
            os.system(f'wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-{es_version}-linux-x86_64.tar.gz -q')
            os.system(f'tar -xzf elasticsearch-{es_version}-linux-x86_64.tar.gz')
        elif platform == 'darwin': # OS X
            # May need to install wget before hand...
            os.system(f'wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-{es_version}-darwin-x86_64.tar.gz -q')
            os.system(f'tar -xzf elasticsearch-{es_version}-darwin-x86_64.tar.gz')
        else:
            # raise Exception('Unknown platform: ' + platform)
            raise NotImplementedError('Unknown platform: ' + platform)
    # os.system(f'sudo chown -R daemon:daemon elasticsearch-{es_version}')
    os.system(f'sudo chmod -R a+rwX elasticsearch-{es_version}') # REMOVING ALL PERMISSION CONSTRAINTS MAY BE DANGEROUS

    from subprocess import Popen, PIPE, STDOUT
    es_server = Popen([f'elasticsearch-{es_version}/bin/elasticsearch'],
                    stdout=PIPE, stderr=STDOUT,
                    start_new_session=True # alternative to line above; may not work
                    )
    if verbose:
        print('Waiting 30s for Elasticsearch to boot...')
    # wait until ES has started
    time.sleep(30)


def preprocess_documents(document_store, verbose=True):
    # Let's first fetch some documents that we want to query
    doc_dir = "data/transcripts"

    # Here: YouTube transcripts
    # s3_url = "https://nolan-b1.s3.us-west-2.amazonaws.com/yt_captions_oneline.tar.gz"
    s3_url = "https://nolan-b1.s3.us-west-2.amazonaws.com/captions_oneline_w_titles.tar.gz"
    success = fetch_archive_from_http(url=s3_url, output_dir=doc_dir)
    if not success:
        print('ERROR: Failed to fetch transcript archive. Data in ' + doc_dir + ' must first be erased.')

    # Convert files to dicts
    # You can optionally supply a cleaning function that is applied to each doc (e.g. to remove footers)
    # It must take a str as input, and return a str.
    docs = convert_files_to_dicts(dir_path=doc_dir)

    # Print the first few docs, as examples
    # print(docs[:3])

    # We now have a list of dictionaries that we can write to our document store.
    # If your texts come from a different source (e.g. a DB), you can of course skip convert_files_to_dicts() and create the dictionaries yourself.
    # The default format here is:
    # {
    #    'text': "<DOCUMENT_TEXT_HERE>",
    #    'meta': {'name': "<DOCUMENT_NAME_HERE>", ...}
    #}
    # (Optionally: you can also add more key-value-pairs here, that will be indexed as fields in Elasticsearch and
    # can be accessed later for filtering or shown in the responses of the Finder)

    # Let's split up our documents into chunks, each chunk becoming it's own document
    if verbose:
        print('Splitting documents and adding metadata...')
    processor = PreProcessor(
        split_by="word",
        split_length=100,
        split_respect_sentence_boundary=False,
        split_overlap=25
    )
    docs_split = []
    for doc in docs:
        id = doc['meta']['name'].split('.')[0]
        i = 0
        close_brackets_seen = 0
        while close_brackets_seen < 2:
            if doc['text'][i] == ']':
                close_brackets_seen += 1
            i += 1
        # i should now point to a space just after the metadata and just before the transcript
        # title_w_brackets = doc['text'][:i]
        # title = re.sub(r'(\[\[ )|( \]\])', '', title_w_brackets)
        bracketed_metadata = doc['text'][:i]
        doc['text'] = doc['text'][i+1:] # remove metadata from document text
        splits = processor.process(doc)
        for split in splits:
            # prepend video metadata to each split so that metadata is used during retrieval
            split['text'] = bracketed_metadata + ' ' + split['text']
            docs_split.append(split)

    # Let's have a look at the first 3 entries:
    # print(docs_split[:3])

    # Delete old documents
    if verbose:
        print('Deleting old documents...')
    document_store.delete_documents()

    # Now, let's write the dicts containing documents to our DB.
    if verbose:
        print('Writing new documents...')
    document_store.write_documents(docs_split)


def retrieve_video_metadata():
    pass