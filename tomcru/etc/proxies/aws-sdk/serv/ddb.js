import proxylib from "../proxylib.js"


export class DocumentClient {
  _proxy(TableName, method, args) {
    proxylib.t_out(proxylib.ser({
      boto3: 'resource',
      serv_id: 'dynamodb',
      resource_type: 'Table', resource_id: TableName,
      method, args
    }));

    return {
      async promise() {
        return proxylib.deser(await proxylib.t_in());
      }
    }
  }

  get({ TableName, ...args }) {
    return this._proxy(TableName, 'get_item', args);
  }

  put({ TableName, ...args }) {
    return this._proxy(TableName, 'put_item', args);
  }

  async update({ TableName, ...args }) {
    return this._proxy(TableName, 'update_item', args);
  }

  delete({ TableName, ...args }) {
    return this._proxy(TableName, 'delete_item', args);
  }

  async scan({ TableName }) {
  }

  async query({ TableName }) {
  }
}

export default {
  DocumentClient
};
