from config import ROOT, API_TOKEN, DATAVERSE_ID
from pyDataverse.api import DataAccessApi, SearchApi, NativeApi
import json
import re

def metadatasearch(queries):
    s = SearchApi(ROOT, API_TOKEN)
    if 'q' in queries:
        q = queries['q']
    else:
        q = '*'

    pids = {}
    if q:
        searchdata = s.search(q, sort='date', per_page=100)
        results = json.loads(searchdata.content)
        pids = {}
        for item in results['data']['items']:
            if 'global_id' in item:
                pids[item['global_id']] = item['description']
    return pids

def get_images(pids):
    urls = {}
    native_api = NativeApi(ROOT, API_TOKEN)
    images = []
    timeline = []
    result = {}

    for doi in pids:
        resp = None
        mediaitem = {}
        url = None
        try:
            try:
                resp = native_api.get_dataset_version(doi, ':latest')
            except:
                resp = native_api.get_dataset_version(doi, ':draft')
        except:
            print("Skip %s" % doi)
        if resp:
            thistext = {}
            dates = {}
            pubdate = process_date(json.loads(resp.content)['data']['createTime'])
            mediaitem['start_date'] = pubdate
            mediaitem['end_date'] = pubdate

            for metadata in json.loads(resp.content)['data']['metadataBlocks']['citation']['fields']:
                if metadata['typeName'] == 'title':
                    thistext['headline'] = metadata['value']
                if metadata['typeName'] == 'dsDescription':
                    thistext['text'] = metadata['value'][0]['dsDescriptionValue']['value']

                if metadata['typeName'] == 'alternativeURL':
                    media = {}
                    media['url'] = metadata['value']
                    url = metadata['value']
                    media['caption'] = ""
                    media['credit'] = ""
                    mediaitem['media'] = media

                    #print(metadata)
                    urls[doi] = metadata['value']
                    try:
                        files = json.loads(resp.content)
                        fileid = files['data']['files'][0]['dataFile']['id']
                        thisitem = {}
                        thisitem['fileid'] = fileid
                        thisitem['image'] = "/images/%s" % fileid
                        thisitem['url'] = metadata['value']
                        media['url'] = thisitem['image']
                        #images.append("/images/%s" % fileid)
                        images.append(thisitem)
                    except:
                        skip = True

            if url:
                if 'text' in thistext:
                    thistext['text'] = "(<a href='%s'>Original</a>) " % url + thistext['text'] 
            mediaitem['text'] = thistext

        timeline.append(mediaitem)
    result['images'] = images
    result['timeline'] = timeline
    return result

def process_date(date_str):
    if re.match("^\d{4}$", date_str):
        return { "year": date_str}
    try:
        year,month,day,hour,minute,sec = re.match("^(\d{4})[/,\-](\d+)[/,\-](\d+)T(\d+)\:(\d+)\:(\d+)",date_str).groups()
        return { "year": year, "month": month, "day": day, "hour": hour, "minute": minute, "second": sec }
    except AttributeError:
        pass

    sys.stderr.write("*** weird date: %s\n" % date_str)
    return {}

