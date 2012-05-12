
import os, csv

from fom.dev import sandbox_fluid
from fom.mapping import Namespace, Object, tag_value


def create_tags():
    ns = Namespace(u'test/medical')
    ns.create(u'Medical tags')
    ns.create_tag(u'date_of_birth', u'Date of birth', True)
    ns.create_tag(u'age', u'Decimal age', True)
    ns.create_tag(u'height', u'Height', True)
    ns.create_tag(u'weight', u'Weight', True)
    ns.create_tag(u'bmi', u'Body Mass Index', True)
    ns.create_tag(u'date', u'Date', True)
    ns.create_tag(u'sex', u'Sex', True)
    ns.create_tag(u'pubertal_stage', u'Pubertal stage')


class Demography(Object):
    date_of_birth = tag_value(u'test/medical/date_of_birth')
    age = tag_value(u'test/medial/age')


class Anthropometry(Object):
    height = tag_value(u'test/medical/height')
    weight = tag_value(u'test/medical/weight')
    bmi = tag_value(u'test/medical/bmi')
    date_of_birth = tag_value(u'test/medical/date_of_birth')
    age = tag_value(u'test/medical/age')
    sex = tag_value(u'test/medical/sex')
    pubertal_stage = tag_value(u'test/medical/pubertal_stage')



class IBDStudy(Demography, Anthropometry):
    """Represents a single set of measurements of the IBD study.
    """

def load_data():
    f = open(os.path.join(os.path.dirname(__file__), 'data.csv'))
    reader = csv.DictReader(f)
    for item in reader:
        o = IBDStudy()
        o.create()
        for k in ['height', 'weight', 'date_of_birth', 'bmi', 'date_of_birth',
                  'age', 'sex', 'pubertal_stage']:
            value = item[k]
            try:
                value = float(value)
            except ValueError:
                pass
            setattr(o, k, value)



if __name__ == '__main__':
    f = sandbox_fluid()
    #create_tags()
    load_data()
    status, response = f.objects.get('test/medical/height > 150.0 and test/medical/bmi > 20.0')
    for uid in response[u'ids']:
        o = IBDStudy(uid)
        print o.height, o.weight, o.bmi

