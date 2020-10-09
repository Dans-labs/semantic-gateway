import xml.dom.minidom
import xml.etree.ElementTree as ET
import re

def readconfig(configfile, params):
   tree = ET.parse(configfile)
   root = tree.getroot()
   vocabs = {}
   if not 'lang' in params:
      params['lang'] = 'en'
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
         else:
             ontodict[o.tag] = o.text 
      vocabs[ontology.attrib.get('name')] = ontodict
          
   return vocabs

file = './conf/gateway.xml'
#file = './conf/termennetwerk.xml'
p = {}
p['term'] = 'test'
c = readconfig(file, p)
print(c)
#print(c['cessda']['apiurl'])
