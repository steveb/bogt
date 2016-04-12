import collections
import json
import os
import sqlite3

from bogt import spec


class BtsDb(object):

    def __init__(self, conf):
        self.conf = conf
        bts_db = os.path.join(conf['bts_db_dir'], 'liveset.db')
        self.conn = sqlite3.connect(bts_db)
        self.categories = spec.table('Patch Category')

    def fetch_liveset_names(self):
        c = self.conn.execute('select id, name, orderNumber from livesets '
                              'order by orderNumber')
        res = c.fetchall()
        liveset_names = collections.OrderedDict()
        for i in res:
            key = '%s: %s' % (i[2], i[1])
            liveset_names[key] = i[0]
        return liveset_names

    def fetch_patch_names(self, liveset_id):
        c = self.conn.execute('select id, name, orderNumber from patches '
                              'where liveSetId = ? '
                              'order by orderNumber', (liveset_id,))
        res = c.fetchall()
        patch_names = collections.OrderedDict()
        for i in res:
            key = '%s: %s' % (i[2], i[1])
            patch_names[key] = i[0]
        return patch_names

    def fetch_patch(self, patch_id):
        c = self.conn.execute(
            'select '
            'id, '
            'liveSetId, '
            'name, '
            'gt100Name1, '
            'gt100Name2, '
            'note, '
            'params, '
            'orderNumber, '
            'logPatchName, '
            'tcPatch, '
            'flag '
            'from patches where id = ?', (patch_id,))

        r = c.fetchone()
        params = json.loads(r[6])
        return {
            "category": self.categories[params['patch_category']],
            "id": r[0],
            "liveSetId": r[1],
            "name": r[2],
            "gt100Name1": r[3],
            "gt100Name2": r[4],
            "note": r[5],
            "params": params,
            "orderNumber": r[7],
            "logPatchName": r[8],
            "tcPatch": r[9],
            "patchID": None,
            "patchNo": None
        }
