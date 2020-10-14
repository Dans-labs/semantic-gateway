import xml.etree.ElementTree as ET

from pydantic import BaseModel


class Vocabularies:
    "This is a Vocabularies class"
    def __init__(self, path):
        self.root = ET.parse(path).getroot()

    def get_ontologies(self):
        ontologies = []
        for i, atype in enumerate(self.root.findall('.//ontology')):
            ontology = Ontology(i, atype)
            ontologies.append(ontology)

        return ontologies

class Ontology:
    def __init__(self, i, element):
        self.i = i
        self.element  = element
    def get_index(self):
        return self.i

    def get_name(self):
        return self.element.attrib['name']

    def get_type(self):
        return self.element.find('type').text

    def get_vocabulary(self):
        v = self.element.find('vocabulary')
        if v is not None:
            return self.element.find('vocabulary').text
        return ''

    def get_base_url(self):
        return self.element.find('api').text

    def get_uri(self):
        u = self.element.find('parameters/uri')
        if u is not None:
            return u.text
        return ''

    def get_vocab(self):
        u = self.element.find('parameters/vocab')
        if u is not None:
            return u.text
        return ''

    def get_query(self):
        u = self.element.find('parameters/query')
        if u is not None:
            return u.text
        return ''

    def get_lang(self):
        u = self.element.find('parameters/lang')
        if u is not None:
            return u.text
        return ''


class WriteXML:
    root = ET.Element('vocabularies');
    def __init__(self, el):
        #Remove all vocabularies children
        for child in self.root.findall('.//ontology'):
            self.root.remove(child)
        for key, value in el:
            if str(value).strip() != '':
                if str(key).startswith('inputName_'):
                    ontology = ET.SubElement(self.root, 'ontology')
                    ontology.set('name',str(value))
                if str(key).startswith('inputType_'):
                    type = ET.SubElement(ontology, 'type')
                    type.text = str(value)
                if str(key).startswith('inputVocabulary_'):
                    voc = ET.SubElement(ontology, 'vocabulary')
                    voc.text = str(value)
                if str(key).startswith('inputBaseUrl_'):
                    api = ET.SubElement(ontology, 'api')
                    api.text = str(value)
                    parameters = ET.SubElement(ontology, 'parameters')

                if str(key).startswith('inputUri_'):
                    uri = ET.SubElement(parameters, 'uri')
                    uri.text = str(value)

                if str(key).startswith('inputVocab_'):
                    vocab = ET.SubElement(parameters, 'vocab')
                    vocab.text = str(value)

                if str(key).startswith('inputQuery_'):
                    query = ET.SubElement(parameters, 'query')
                    query.text = str(value)

                if str(key).startswith('inputLang_'):
                    lang = ET.SubElement(parameters, 'lang')
                    lang.text = str(value)

        # create a new XML file with the results
    def save(self, path):
        mydata = ET.tostring(self.root, encoding='UTF8', method='xml')
        myfile = open(path, 'wb')
        myfile.seek(0)
        myfile.truncate()
        myfile.seek(0)
        myfile.write(mydata)
        myfile.close()