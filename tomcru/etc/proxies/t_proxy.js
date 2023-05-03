import { handler } from "./index.js";

// deserialize lambda context
const [node_bin, script_path, events_json_b64] = process.argv;

if (!events_json_b64) {
  throw "No lambda events passed";
}

const events = JSON.parse(Buffer.from(events_json_b64, 'base64').toString('utf8'));

events['js_output'] = 'hey_i_exist';
events['FS_PATH_ENVVAR'] = process.env.FS_PATH || null;

const response = Buffer.from(JSON.stringify(events), 'utf8').toString('base64');

process.stdout.write(response)
