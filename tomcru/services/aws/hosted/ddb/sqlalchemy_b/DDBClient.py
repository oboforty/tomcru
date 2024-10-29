import decimal
import json
import re
from copy import deepcopy

from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified

from botocore.exceptions import ClientError
try:
    from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
except:
    # todo: redefine TypeDeserializer
    raise

from .DDBSqlAlchemyTable import DDBSqlAlchemyTable


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


DDB_TYPE_KEYS = {'S', 'N', 'B', 'BOOL', 'NULL', 'M', 'L', 'SS', 'NS', 'BS'}


class DDBClient:
    """AWS Endpoint client"""

    def __init__(self, tables):
        self._tables: dict[str, DDBSqlAlchemyTable] = tables
        self._deserializer = TypeDeserializer()
        self._serializer = TypeSerializer()

    def serialize(self, resp):
        return self._serializer.serialize(resp)

    def deserialize(self, resp):
        if not set(resp.keys()) & DDB_TYPE_KEYS:
            resp = {"M": resp}
        return self._deserializer.deserialize(resp)

    def aws_integ_parse_response(self, serv_id, region, response):

        #return """{"Item":{"M":{"yolo":{"BOOL":true},"items":{"M":{"cnt":{"N":"2"}}},"eid":{"S":"kecske"}}}}"""
        ATTR_TO_SERIALIZE = ('Attributes', 'Key', 'Item', 'Items')

        # for attr in ATTR_TO_SERIALIZE:
        #     if attr in response:
        #         response[attr] = self.deserialize(response[attr])

        return json.dumps(response, separators=(',', ":"), cls=DecimalEncoder)

    def GetItem(self, TableName, Key, **kwargs):
        Key = self.deserialize(Key)
        table = self._tables[TableName]
        ent = table._get_ent(Key)

        if not ent:
            return {}

        return {
            'Item': ent.ddb_content
        }

    def PutItem(self, TableName, Item, ReturnValues=None, **kwargs):
        ItemSer = Item
        Item = self.deserialize(Item)
        table = self._tables[TableName]
        # check if already exists
        key = table._get_key(Item)
        ent = table._get_ent(key)

        if not ent:
            ent = table.T()

            setattr(ent, table.partition_key, key[table.partition_key])
            if table.sort_key:
                setattr(ent, table.sort_key, key[table.sort_key])

            setattr(ent, 'ddb_content', ItemSer)
        else:
            ent.ddb_content = ItemSer

        table.session.add(ent)
        if table._autocommit:
            table.session.commit()

        return {}
        #if not ReturnValues or ReturnValues == 'NONE'elif ReturnValues == 'ALL_OLD': return {'Attributes': ItemSer}

    def DeleteItem(self, TableName, Key, **kwargs):
        Key = self.deserialize(Key)
        table = self._tables[TableName]

        # check if already exists
        ent = table._get_ent(Key)

        if not ent:
            raise ClientError("not_found", None)
        else:
            table.session.delete(ent)

            if table._autocommit:
                table.session.commit()

        return {}

    def UpdateItem(self, TableName, Key, UpdateExpression, ExpressionAttributeValues=None, ExpressionAttributeNames=None, ConditionExpression=None, ReturnValues=None):
        # deserialize input
        Key = self.deserialize(Key)
        for k in ExpressionAttributeValues:
            ExpressionAttributeValues[k] = self._deserializer.deserialize(ExpressionAttributeValues[k])

        # find entity
        table = self._tables[TableName]
        ent = table._get_ent(Key)

        if not ent:
            raise Exception("404 ent?")

        content = self.deserialize(ent.ddb_content)
        old_content_ser = deepcopy(ent.ddb_content)

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
        for match in re.finditer(r"\([a-zA-Z_0-9\s:#]*(,)[a-zA-Z_0-9\s:#]*\)", UpdateExpression):
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

            # update and serialize
            # todo: old content ser is ok, content is bad
            ddb_content = self.deserialize(ent.ddb_content)
            ddb_content.update(content)
            ent.ddb_content = self.serialize(ddb_content)['M']
            flag_modified(ent, 'ddb_content')

            table.session.commit()
        else:
            raise NotImplementedError(method + " method DDB")

        # todo: @later filter only changed
        if 'ALL_NEW' == ReturnValues or 'UPDATED_NEW' == ReturnValues or not ReturnValues:
            return {"Attributes": ent.ddb_content}
        elif 'ALL_OLD' == ReturnValues or 'UPDATED_OLD' == ReturnValues:
            return {"Attributes": old_content_ser}

        raise NotImplementedError(ReturnValues)

    def query(self, TableName, ExpressionAttributeValues=None, KeyConditionExpression=None, IndexName=None, **kwargs):
        table = self._tables[TableName]

        # if ExpressionAttributeValues:
        #     for k,v in ExpressionAttributeValues.items():
        #         KeyConditionExpression = KeyConditionExpression.replace(k, str(v))
        Q, T = table.sql()

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

            attributes = table.T._indexes[IndexName]
            #Q = self.session.query(*map(lambda attr: getattr(self.T, attr), attributes))
        else:
            attributes = 'ALL'

        return {
            'Items': [{k:v for k,v in r.ddb_content.items() if k in attributes or attributes == 'ALL'} for r in result]
        }

    def BatchGetItem(self, RequestItems):
        items = {}
        err = {}

        for TableName, commands in RequestItems.items():
            items[TableName] = []

            for key in commands['Keys']:
                resp = self.GetItem(TableName=TableName, Key=key)
                if 'Item' in resp:
                    items[TableName].append(resp['Item'])
                else:
                    err.setdefault(TableName, {"Keys": []})
                    err[TableName]['keys'].append(key)

        return {
            'Responses': items,
            'ConsumedCapacity': [],
            'UnprocessedKeys': err
        }

    def BatchWriteItem(self, RequestItems, **kwargs):
        for TableName, commands in RequestItems.items():
            table = self._tables[TableName]

            autocommit = table._autocommit
            table._autocommit = False

            # todo: handle response and if not inserted, append UnprocessedItems
            for command in commands:
                if 'PutRequest' in command:
                    self.PutItem(TableName=TableName, Item=command['PutRequest']['Item'])
                if 'DeleteRequest' in command:
                    self.DeleteItem(TableName=TableName, Key=command['DeleteRequest']['Key'])

            table.session.commit()
            table._autocommit = autocommit

        return {
            'ConsumedCapacity': [],
            'ItemCollectionMetrics': {},
            'UnprocessedItems': {}
        }
