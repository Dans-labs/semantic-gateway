import io
import urllib3
import json

from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from starlette.responses import FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

from src.model import Vocabularies, WriteXML

app = FastAPI()
templates = Jinja2Templates(directory='templates/')
app.mount('/static', StaticFiles(directory='static'), name='static')

conf_file_path = './data/gateway.xml'
http = urllib3.PoolManager()

@app.get('/')
def info():
    return {"name":"semantic gateway", "version":"1.0"}

@app.get('/configuration/xml')
def get_configuration_xml():
    try:
        content = open(conf_file_path, 'r')
        return Response(content=content.read(), media_type="application/xml")
    except:
        return "NOT FOUND"

@app.get('/configuration/view')
def get_configuration_html_view(request: Request):
    vocabularies = Vocabularies(conf_file_path)
    return templates.TemplateResponse('configuration-view.html', context={'request': request, 'ontologies': vocabularies.get_ontologies()})

@app.get('/configuration/edit')
def get_configuration_html_view(request: Request):
    vocabularies = Vocabularies(conf_file_path)
    return templates.TemplateResponse('configuration-edit.html', context={'request': request, 'ontologies': vocabularies.get_ontologies()})

@app.post("/configuration/edit")
async def modify_configuration_post(request: Request):
    form_data = await request.form()
    writeXML = WriteXML(form_data.items());
    writeXML.save(conf_file_path)
    return RedirectResponse(url='/configuration/view', status_code=302)

@app.get('/configuration/download')
def download():
    return FileResponse(conf_file_path, media_type='application/octet-stream', filename='gateway-conf.xml')

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

        vocabularies = Vocabularies(conf_file_path)
    return templates.TemplateResponse('dv-cvm-setting-generator.html', context={'request': request, 'dv_setting_json' : dv_setting_json, 'ontologies': vocabularies.get_ontologies()})