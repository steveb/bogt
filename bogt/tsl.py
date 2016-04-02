
import collections
import json


def load_tsl_from_file(path):
    with open(path) as f:
        return LiveSet(json.load(f))


class LiveSet(object):

    def __init__(self, data):
        self.data = data
        self.patches = collections.OrderedDict()
        for p in data.get('patchList', []):
            key = '%s: %s' % (p.get('orderNumber'), p.get('name').strip())
            self.patches[key] = p
