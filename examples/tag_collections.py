# coding: utf-8


"""Example of Many-to-many relationships in fluiddb with Fom"""


from fom.mapping import Object, tag_collection, tag_value


class Disease(Object):

    symptoms = tag_collection(u'test/symptoms',
                              foreign_tagpath=u'test/diseases')

    def __repr__(self):
        return '<Disease: %s>' % self.about


class Symptom(Object):

    diseases = tag_collection(u'test/diseases', map_type=Disease)

    def __repr__(self):
        return '<Symptom: %s>' % self.about


# XXX well this is going to have to improve!
Disease.__dict__['symptoms'].map_type = Symptom


if __name__ == '__main__':
    from fom.dev import sandbox_fluid
    sandbox_fluid()
    chest_pain = Symptom(about='symptom:Chest Pain')
    heartburn = Symptom(about='symptom:Heartburn')
    dizziness = Symptom(about='symptom:Dizziness')
    ischaemic_heart_disease = Disease(about='disease:Ischaemic Hear Disease')
    ischaemic_heart_disease.symptoms.add(chest_pain)
    ischaemic_heart_disease.symptoms.add(dizziness)
    gastric_ulcer = Disease(about='disease:Gastric Ulcer')
    gastric_ulcer.symptoms.add(chest_pain)
    gastric_ulcer.symptoms.add(heartburn)
    print 'Ischaemic Heart Disease', ischaemic_heart_disease.symptoms
    print 'Gastric Ulcer', gastric_ulcer.symptoms
    print 'Chest Pain', chest_pain.diseases
    print 'Heartburn', heartburn.diseases
    print 'Dizziness', dizziness.diseases



