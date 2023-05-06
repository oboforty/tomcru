
export const ser = (o) => Buffer.from(JSON.stringify(o), 'utf8').toString('base64');

export const deser = (s) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));

export const t_out = (s) => process.stdout.write(s+"\n");

export const t_in = () => {return new Promise((resolve) => {
  const cb = (chunk) => resolve(chunk.trim());
  setTimeout(()=>resolve(ser({"err": "timeout"})), 2000);
  process.stdin.once("data", cb);
})};

export const delay = time => new Promise(resolve=>setTimeout(resolve,time));

export default {
  t_in, t_out, ser, deser
}