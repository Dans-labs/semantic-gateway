#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uvicorn
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import xml.etree.ElementTree as ET
import requests
import re
import os
import json
import urllib3, io
import os

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Semantic Gateway API",
        description="Semantic Gateway is Linked Open Data framework for Dataverse.",
        version="0.1",
        routes=app.routes,
    )

    openapi_schema['tags'] = tags_metadata

    app.openapi_schema = openapi_schema
    return app.openapi_schema

tags_metadata = [
    {
        "name": "country",
        "externalDocs": {
            "description": "Put this citation in working papers and published papers that use this dataset",
            "authors": 'Slava Tykhonov',
            "url": "https://dans.knaw.nl/en",
        },
    },
    {
        "name": "namespace",
        "externalDocs": {
            "description": "Endpoint to serve namespaces for Controlled Vocabularies",
            "authors": 'Slava Tykhonov',
            "url": "https://ns.coronawhy.org",
        },
    }
]

app = FastAPI(
    openapi_tags=tags_metadata
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex='https?://.*',
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.openapi = custom_openapi

http = urllib3.PoolManager()

@app.get("/{vocab}/{term}/", tags=["namespace"])
def namespace(vocab: str, term: str, request: Request):
    #return request.query_params
    return "%s %s" % (vocab, term)

# READ configuration
def readconfig(iparams):
   configfile = '/app/conf/gateway.xml'
   if 'config' in os.environ:
       configfile = os.environ['config']

   tree = ET.parse(configfile)
   root = tree.getroot()
   vocabs = {}
   params = {}
   params['type' ] = 'unknown'
   for k in iparams:
      params[k] = iparams[k]
   if 'voc' in iparams:
      params['vocab'] = iparams['voc']
      del params['voc']
   if not 'lang' in params:
      params['lang'] = 'en'
   if 'keyword' in params:
      params['term'] = "%s*" % params['keyword']
   if 'code' in params:
      params['term'] = "%s*" % params['code']
      params['query'] = "%s*" % params['code']
   if 'term' in params:
      params['term'] = "%s*" % params['term']

   for ontology in root.iter('ontology'):
      ontodict = {}
      for o in ontology:
         apiurl = "%s" % ontology.find('api').text
         if ontology.find('uri').text:
             apiurl = "%s/%s" % (apiurl, ontology.find('uri').text)
         else:
             apiurl = "%s/" % apiurl
         if str(o.tag) == 'parameters':
             apiurl = "%s?" % apiurl
             for p in ontology.find('parameters'):
                 apiurl = "%s%s=%s&" % (apiurl, p.tag, p.text)
             apiurl = apiurl[:-1]
             ontodict['apiurltemplate'] = apiurl
             for p in params:
                 apiurl = re.sub("\$%s" % p, params[p], apiurl)
             ontodict['apiurl'] = apiurl
         elif str(o.tag) == 'query':
             query = "%s" % ontology.find('query').text
             for p in params:
                 query = re.sub("\$%s" % p, params[p], query)
             ontodict['query'] = query
         elif str(o.tag) == 'uri':
             uri = "%s" % ontology.find('uri').text
             for p in params:
                 uri = re.sub("\$%s" % p, params[p], uri)
             ontodict['uri'] = uri
         else:
             ontodict[o.tag] = o.text
      if ontodict['type'] == 'nde':
         ontodict['apiurl'] = "%s/%s?%s" % (ontodict['api'], ontodict['uri'], ontodict['query'])
      elif ontodict['type'] == 'cessda':
         ontodict['apiurl'] = "%s/%s" % (ontodict['api'], ontodict['uri'])
         ontodict['apiurl'] = ontodict['apiurl'][:-1]
      vocabs[ontology.attrib.get('name')] = ontodict

   if 'vocab' in params:
      try:
          return vocabs[params['vocab']]
      except:
          return {}

   return vocabs

@app.route("/vocabs")
def vocabs(request: Request):
    config = readconfig(request.query_params)
    return str(config)

@app.get("/")
def search(request: Request):
    input = request.query_params
 
    test = {}
    test['vocab'] = 'unesco'
    if 'keyword' in input:
        test['keyword'] = input['keyword']
    if 'code' in input:
        test['keyword'] = input['code']
    #input = test
    
    # CONFIG
    config = readconfig(input)

    if config['type'] == 'skosmos':
        data = skosmos(config)
        return data
    elif config['type'] == 'nde':
        data = nde(config)
        return data
    elif config['type'] == 'cessda':
        data = cessda(config)
        return data
    return config

def cessda(config):
    data = json.loads(requests.get(config['apiurl']).text)
    result = data
    return result

def nde(config):
    data = json.loads(requests.get(config['apiurl']).text)
    result = data['data']['terms'][0]['terms']
    dataset = {}
    alldata = []
    for item in result:
        d = {}
        url = {}
        prefLabel = {}
        if 'uri' in item:
            url['type'] = 'uri'
            url['value'] = item['uri']
            prefLabel["type"] = "literal"
            prefLabel['value'] = str(item['altLabel'][0])
            d['url'] = url
            d['prefLabel'] = prefLabel
            alldata.append(d)
    if result:
        dataset['listOfCodes'] = alldata
    return dataset

def skosmos(config):
    data = json.loads(requests.get(config['apiurl']).text)
    result = data['results']
    dataset = {}
    alldata = []
    for item in result:
        d = {}
        url = {}
        prefLabel = {}
        if 'uri' in item:
            url['type'] = 'uri'
            url['value'] = item['uri']
            prefLabel["type"] = "literal"
            prefLabel['value'] = str(item['prefLabel'])
            d['url'] = url
            d['prefLabel'] = prefLabel
            alldata.append(d)
    if result:
        dataset['listOfCodes'] = alldata
    return dataset

def create_json_cvmm(code):
    r = http.request('GET', "https://raw.githubusercontent.com/ekoi/speeltuin/master/resources/CMM_Custom_MetadataBlock.tsv")
    d = r.data.decode('utf-8')
    s = io.StringIO(d)

    cvmm_json_result = {}
    cv_json = []
    start_cvm = False

    for line in s:
        if start_cvm:
            # print(line)
            abc = line.split('\t')
            o_obj = {}
            # print(abc[3])

            if code is None:
                cv_json.append(create_cmm_element(abc[3],abc[2],abc[2],abc[2]))

            elif code in abc[3]:
                cv_json.append(create_cmm_element(abc[3],abc[2],abc[2],abc[2]))


        if line.startswith('#controlledVocabulary'):
            start_cvm = True

    cvmm_json_result['listOfCodes'] = cv_json
    json_data = json.dumps(cvmm_json_result)

    return json_data

def create_json_cvm_dataverse(code):
    r = http.request('GET', "https://raw.githubusercontent.com/ekoi/speeltuin/master/resources/CMM_Custom_MetadataBlock.tsv")
    d = r.data.decode('utf-8')
    s = io.StringIO(d)

    cvmm_json_result = {}
    cv_json = []
    start_datasetfield = False

    for line in s:
        if line.startswith('#controlledVocabulary'):
            start_datasetfield = False
        if start_datasetfield:
            # print(line)
            abc = line.split('\t')
            o_obj = {}

            if code is None:
                cv_json.append(create_cmm_element(abc[16],abc[2],abc[2],abc[2]))

            elif code in abc[16]:
                cv_json.append(create_cmm_element(abc[16],abc[2],abc[2],abc[2]))

        if line.startswith('#datasetField'):
            start_datasetfield = True

    cvmm_json_result['listOfCodes'] = cv_json
    json_data = json.dumps(cvmm_json_result)

    return json_data

def create_cmm_element(u, c, pl, lpl):
    o_obj = {}
    o_obj['url'] = {'type': 'uri', 'value': u}
    o_obj['code'] = {'type': 'literal', 'value': c}
    o_obj['prefLabel'] = {'type': 'literal', 'value': pl}
    o_obj['languagePrefLabel'] = {'type': 'literal', 'value': lpl}
    o_obj['language'] = {'type': 'literal', 'value': 'en'}
    return o_obj

#if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0", port=9266)
#if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0")
