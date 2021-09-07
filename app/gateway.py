#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Developed by Slava Tykhonov and Eko Indarto
# Data Archiving and Networked Services (DANS-KNAW), Netherlands
import uvicorn
import pandas as pd
from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from starlette.responses import FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from src.model import Vocabularies, WriteXML
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import xml.etree.ElementTree as ET
import requests
import re
import os
import json
import urllib3, io
import subprocess
from dateutil.parser import parse

def datecheck(string, fuzzy=False):
    dates = []
    candidates = string.split('-')
    if is_date(candidates[0]):
        for x in candidates:
            dates.append(is_date(str(x)))
    return dates

def is_date(string, fuzzy=False):
    try:
        x = parse(string, fuzzy=fuzzy)
        return x

    except ValueError:
        return False

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
templates = Jinja2Templates(directory='templates/')
app.mount('/static', StaticFiles(directory='static'), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex='https?://.*',
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.openapi = custom_openapi
configfile = '/app/conf/gateway.xml'
if 'config' in os.environ:
    configfile = os.environ['config']
http = urllib3.PoolManager()

@app.get('/configuration/xml')
def get_configuration_xml():
    try:
        content = open(configfile, 'r')
        return Response(content=content.read(), media_type="application/xml")
    except:
        return "NOT FOUND"

@app.get('/configuration/view')
def get_configuration_html_view(request: Request):
    vocabularies = Vocabularies(configfile)
    return templates.TemplateResponse('configuration-view.html', context={'request': request, 'ontologies': vocabularies.get_ontologies()})

@app.get('/configuration/edit')
def get_configuration_html_view(request: Request):
    vocabularies = Vocabularies(configfile)
    return templates.TemplateResponse('configuration-edit.html', context={'request': request, 'ontologies': vocabularies.get_ontologies()})

@app.post("/configuration/edit")
async def modify_configuration_post(request: Request):
    form_data = await request.form()
    writeXML = WriteXML(form_data.items());
    writeXML.save(configfile)
    return RedirectResponse(url='/configuration/view', status_code=302)

@app.get('/configuration/download')
def download():
    return FileResponse(configfile, media_type='application/octet-stream', filename='gateway-conf.xml')

def datareader(dataverseURL, fileid):
    try:
        fileURL = "https://%s/api/access/datafile/%s?format=original&gbrecs=true" % (dataverseURL, fileid)
        df = pd.read_csv(fileURL)
    except:
        fileURL = "http://%s/api/access/datafile/%s?format=original&gbrecs=true" % (dataverseURL, fileid)
        df = pd.read_csv(fileURL)
    try:
        datarecords = df.to_json(orient='records')
        return (df, datarecords)
    except:
        return "{ 'error': 'Not supported format' }"

# Data files conversion to the Semantic Bot format, for example: /records/dataverse.harvard.edu/4436990/
@app.get("/records/{dataverseURL}/{fileid}/", tags=["namespace"])
def records(dataverseURL: str, fileid: str, request: Request):
    #fileURL = 'https://dataverse.harvard.edu/api/access/datafile/4436989?format=original&gbrecs=true'
    MAX = 2
    (df, datarecords) = datareader(dataverseURL, fileid)

    records = []
    links = []
    result = {}
    for i in range(0,MAX):
        datarec = {}
        record = {}
        record['id'] = i
        record['host'] = dataverseURL
        record['fileid'] = fileid
        record['size'] = MAX
        record['fields'] = json.loads(datarecords)[i]
        datarec['record'] = record
        records.append(datarec)
    result['links'] = [ fileURL ]
    result['records'] = records
    return result

# Data catalogue API conversion
fileURL = 'https://dataverse.harvard.edu/api/access/datafile/4436989?format=original&gbrecs=true'
@app.get("/catalog/{dataverseURL}/{fileid}/", tags=["namespace"])
def records(dataverseURL: str, fileid: str, request: Request):
    dataset_id = "%s@%s" % (dataverseURL, fileid)
    (df, datarecords) = datareader(dataverseURL, fileid)
    datatypes = df.dtypes.replace('object', 'text')
    fieldtypes = {}
    for index, value in datatypes.items():
        fieldtypes[index] = str(value)
    r = json.loads(datarecords)
    records = []
    links = []
    result = {}
    fields = []
    for i in range(0,1):
        f = []
        for field in r[i]:
            fieldtype = 'text'
            if field in fieldtypes:
                fieldtype = fieldtypes[field]
            thisfield = {
"label": field,
"type": fieldtype,
"description": r[i][field],
"name": field
            }
            fields.append(thisfield)
        
    result['metadata'] = 'metadata'
    result['fields'] = fields

    jsonurl = "https://data.opendatasoft.com/api/datasets/1.0/coronavirus-covid-19-pandemic-worldwide-data@bruxellesdata/"
    r = requests.get(jsonurl)
    data = r.json()
    data['fields'] = fields
    #data['datasetid'] = dataset_id
    return data
    return result

@app.get("/isdate/{thisdate}/", tags=["namespace"])
def datevalidation(thisdate: str, request: Request):
    dates = []
    result = {}
    result['item'] = thisdate
    result['date'] = datecheck(thisdate)
    output = {}
    output['raw'] = result
    if 'date' in result:
        jsonld = {}
        values = {}
        values['value'] = result['date']
        jsonld['http://purl.org/dc/terms/date'] = values 
        output['jsonld'] = jsonld
    return output

@app.get("/{vocab}/{term}/", tags=["namespace"])
def namespace(vocab: str, term: str, request: Request):
    artnamespace = {}
    artnamespace['ns'] = vocab
    artnamespace['term'] = term
    return artnamespace
    #return "%s %s" % (vocab, term)

@app.get("/wikidata/{operation}/{term}/", tags=["namespace"])
def namespace(operation: str, term: str, request: Request):
    artnamespace = {}
    words = []
    words = re.findall('[A-Z][^A-Z]*', term)    
    keywords = " " 
    keywords = keywords.join(str(x) for x in words)
    command = "/usr/bin/wd %s -l en -j %s" % (operation, str(keywords))
    print(command)
    output = subprocess.run(command.split(), stdout=subprocess.PIPE)
    artnamespace['operation'] = operation
    artnamespace['term'] = term
    artnamespace['result'] = json.loads(output.stdout)
    return artnamespace

@app.get("/wikitaxonomy/{termid}/{operation}/", tags=["namespace"])
def namespace(termid: str, operation: str, request: Request):
    artnamespace = {}
    command = "/usr/bin/wdtaxonomy %s -l en -j %s" % (termid, operation)
    print(command)
    output = subprocess.run(command.split(), stdout=subprocess.PIPE)
    artnamespace['operation'] = operation
    artnamespace['term'] = termid
    artnamespace['result'] = json.loads(output.stdout)
    return artnamespace

# READ configuration
def readconfig(iparams):
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
   if 'query' in params:
      params['term'] = "%s*" % params['query']
      params['query'] = "%s*" % params['query']

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
    protocol = 'default'
    if 'protocol' in input:
        protocol = input['protocol']
    try:
        config = readconfig(input)
    except:
        print("Semantic Gateway v0.5")

    if not 'type' in config:
        return config
    if config['type'] == 'skosmos':
        data = skosmos(config, protocol)
        return data
    elif config['type'] == 'nde':
        data = nde(config)
        return data
    elif config['type'] == 'cessda':
        data = cessda(config)
        return data
    return config

@app.get('/dv/setting/edit')
def get_fields_composer(request: Request):
    r = http.request('GET', "https://raw.githubusercontent.com/ekoi/speeltuin/master/resources/CMM_Custom_MetadataBlock.tsv")
    d = r.data.decode('utf-8')
    s = io.StringIO(d)
    template='{"aci":"ACI","source-name":"CVM_SERVER_NAME", "source-url":"CVM_SERVER_URL","vocabs":["VOC"],"keys": ["KV","KT","KU"]}';
    json_process = ''
    json_element = ''
    json_text = ''
    dv_setting_json = []
    dv_setting_el = {}
    for line in s:
        abc = line.split('\t')
        if json_process == '' and abc[1].endswith('-cv'):
            json_element = template.replace('CVM_SERVER_NAME', 'CVM_SERVER_NAME-' + abc[1])
            json_element = json_element.replace('CVM_SERVER_URL', 'CVM_SERVER_URL-' + abc[1])
            json_element = json_element.replace('ACI',abc[1])
            json_element = json_element.replace('VOC', abc[2])
            json_process='create'
        elif json_process  == 'create':
            if abc[1].endswith('-vocabulary'):
                json_element = json_element.replace('KV', abc[1])
            elif abc[1].endswith('-term'):
                json_element = json_element.replace('KT', abc[1])
            elif abc[1].endswith('-url'):
                json_element = json_element.replace('KU', abc[1])
                json_process="finish";
                dv_setting_el = json.loads(json_element)
                dv_setting_json.append(dv_setting_el)

            else:
                print('error')

        if json_process == 'finish':
            json_process = ''

        vocabularies = Vocabularies(configfile)
    return templates.TemplateResponse('dv-cvm-setting-generator.html', context={'request': request, 'dv_setting_json' : dv_setting_json, 'ontologies': vocabularies.get_ontologies()})

def cessda(config):
    data = json.loads(requests.get(config['apiurl']).text)
    result = data
    return result

def nde(config):
    data = json.loads(requests.get(config['apiurl']).text)
    result = data['data']['terms'][0]['terms']
    dataset = {}
    alldata = []
    known = {}
    for item in result:
        d = {}
        url = {}
        prefLabel = {}
        if 'uri' in item:
            if not item['uri'] in known:
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

def skosmos(config, protocol):
    # SKOSMOS filter
    dataset = {}
    alldata = []
    known = {}

    data = json.loads(requests.get(config['apiurl']).text)
    if protocol == 'skosmos':
        result = data['results']
        dataset['@context'] = data['@context']
        for item in result:
            d = {}
            url = {}
            prefLabel = {}
            if 'uri' in item:
                if not item['uri'] in known:
                    d = item
                    alldata.append(d)
                    known[item['uri']] = d
        dataset['results'] = alldata
        return dataset

    result = data['results']
    for item in result:
        d = {}
        url = {}
        prefLabel = {}
        if 'uri' in item:
            if not item['uri'] in known:
                url['type'] = 'uri'
                url['value'] = item['uri']
                prefLabel["type"] = "literal"
                prefLabel['value'] = str(item['prefLabel'])
                d['url'] = url
                d['prefLabel'] = prefLabel
                alldata.append(d)
                known[item['uri']] = url
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9266)
#if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0")
