import re
from sqlalchemy.orm.attributes import flag_modified

from botocore.exceptions import ClientError
from sqlalchemy import text


class DdbTableAdapter:
    def __init__(self, sess, ent_obj, autocommit=True):
        self.T = ent_obj
        self.session = sess
        self.table_name = self.T.__tablename__

        self.partition_key = ent_obj.partition_key
        self.sort_key = ent_obj.sort_key
        self._autocommit = autocommit

    def _get_ent(self, Key):
        if self.sort_key:
            _reldbkey = (Key[self.partition_key], Key[self.sort_key])
        else:
            _reldbkey = Key[self.partition_key]

        ent = self.session.query(self.T).get(_reldbkey)

        return ent

    def get_item(self, Key, **kwargs):
        ent = self._get_ent(Key)

        if not ent:
            return None

        #self.ent2dict(ent)
        return {
            'Item': ent.ddb_content
        }

    def put_item(self, Item, **kwargs):
        # check if already exists
        ent = self._get_ent(self._get_key(Item))

        if not ent:
            ent = self.T(**Item)
        else:
            ent.ddb_content = Item

        self.session.add(ent)

        if self._autocommit:
            self.session.commit()

        return {'Item': ent.ddb_content}

    def delete_item(self, Key, **kwargs):
        # check if already exists
        ent = self._get_ent(Key)

        if not ent:
            raise ClientError("not_found", None)
        else:
            self.session.delete(ent)

            if self._autocommit:
                self.session.commit()

        return True

    def update_item(self, Key, UpdateExpression, ExpressionAttributeValues=None, ExpressionAttributeNames=None, ConditionExpression=None, ReturnValues=None):
        ent = self._get_ent(Key)

        if not ent:
            raise Exception("404 ent?")

        content = ent.ddb_content
        old_content = content.copy()

        if ConditionExpression:
            # evaluate conditions myself bruv
            for condi in ConditionExpression.split(' AND '):
                if ' = ' in condi:
                    # fetch value recursive (e.g. items.gold)
                    condi = condi.split('=')
                    attrs = condi[0].strip().split('.')
                    _val = content
                    for attr in attrs:
                        _val = _val[attr]

                    # now compare parsed values
                    if str(_val) == str(condi[1].strip()):
                        raise ClientError(error_response={
                            "Error": {
                                "Code": "ConditionalCheckFailedException"
                            }
                        }, operation_name=0)
                else:
                    print("!!! NOT IMPLEMENTED !!! ", "Conditional", condi)


        # replace commas in functions

        for match in re.finditer(r"\([a-zA-Z_0-9\s:#]*(\,)[a-zA-Z_0-9\s:#]*\)", UpdateExpression):
            fos = UpdateExpression[match.start():match.end()]
            UpdateExpression = UpdateExpression.replace(fos, fos.replace(',',';'))

        # if all checks are OK, apply update to relDB
        parts = UpdateExpression.split(',')
        method = parts[0].split(' ')[0].lower()

        if 'set' == method:

            for _expr in UpdateExpression[4:].split(','):
                if '=' in _expr:
                    # fetch value recursive (e.g. items.gold)
                    _expr = _expr.split('=')
                    attrs = _expr[0].strip().split('.')
                    _val = content
                    for attr in attrs[:-1]:
                        if attr.startswith('#'):
                            attr = ExpressionAttributeNames[attr]
                        _val = _val[attr]

                    # set value and copy its type
                    attr = attrs[-1]

                    if attr.startswith('#'):
                        attr = ExpressionAttributeNames[attr]
                    _old_val = _val.get(attr)
                    _old_val_type = type(_old_val) if _old_val else None

                    if 'list_append' in _expr[1]:
                        # append to list
                        obj_name, _bind_name = _expr[1].split(';')
                        obj_name = obj_name.strip().split('(')[1].strip()
                        _bind_name = _bind_name.strip().rstrip(')')

                        _new_val = ExpressionAttributeValues[_bind_name]
                        _old_val.append(_new_val)
                    else:
                        # set value
                        _bind_name = _expr[1].strip()
                        # if _old_val_type == type(None):
                        #     # oh shit, let's try to guess the type
                        #     if _new_val.isnumeric():
                        #         _old_val_type = int
                        #     else:
                        #         _old_val_type = type(_new_val)
                        # _new_val = _old_val_type(_new_val)
                        _new_val = ExpressionAttributeValues[_bind_name]
                        _val[attr] = _new_val
                else:
                    raise NotImplementedError(_expr + " " + UpdateExpression)

            ent.ddb_content.update(content)
            flag_modified(ent, 'ddb_content')

            self.session.commit()
        else:
            raise NotImplementedError(method + " method DDB")

        if 'ALL_NEW' == ReturnValues:
            pass
            return {"Item": content, "Attributes": content}
        elif 'ALL_OLD' == ReturnValues:
            return {"Item": old_content, "Attributes": old_content}
        # elif 'CHANGED_NEW' == ReturnValues:
        # elif 'CHANGED_OLD' == ReturnValues:
        raise NotImplementedError()

    def query(self, ExpressionAttributeValues=None, KeyConditionExpression=None, IndexName=None, **kwargs):
        # if ExpressionAttributeValues:
        #     for k,v in ExpressionAttributeValues.items():
        #         KeyConditionExpression = KeyConditionExpression.replace(k, str(v))
        Q = self.session.query(self.T)

        _exprs = KeyConditionExpression.split(' AND ')
        for _expr in _exprs:
            if ' = ' in _expr:
                attr, _exkey = _expr.split(' = ')
                val = ExpressionAttributeValues[_exkey]

                Q = Q.filter(text(f"ddb_content->>'{attr}' = '{val}'"))
            else:
                print("!! NOT IMPLEMENTED FILTER !!", _expr)
                # result.append(ent)

        result = Q.all()

        if IndexName:
            print("[] Querying with index:", IndexName)

            attributes = self.T._indexes[IndexName]
            #Q = self.session.query(*map(lambda attr: getattr(self.T, attr), attributes))
        else:
            attributes = 'ALL'

        return {
            'Items': [{k:v for k,v in r.ddb_content.items() if k in attributes or attributes == 'ALL'} for r in result]
        }

    def batch_get_items(self, RequestItems, **kwargs):

        return {
            'Responses': items
        }

    def batch_writer(self, **kwargs):
        return DdbTableAdapter(self.session, self.T, autocommit=False)

    def batch_reader(self, **kwargs):
        return DdbTableAdapter(self.session, self.T)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # batch writer used in a python contexts uses autocommit=False
        self.session.commit()

    def _get_key(self, Item):
        if not isinstance(Item, dict):
            Item = Item['ddb_content']

        if self.partition_key not in Item:
            print("WTF???", Item, self.partition_key)

        _key = {
            self.partition_key: Item[self.partition_key]
        }

        if self.sort_key:
            _key[self.sort_key] = Item[self.sort_key]

        return _key

    def _truncate(self):
        self.session.execute(f'''TRUNCATE TABLE "{self.table_name}"''')
        self.session.commit()
