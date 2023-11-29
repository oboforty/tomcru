import { handler } from "./index.js";


const proxylib = {
  ser: (o) => Buffer.from(JSON.stringify(o), 'utf8').toString('base64'),

  deser: (s) => JSON.parse(Buffer.from(s, 'base64').toString('utf8')),

  t_out: (s) => process.stdout.write(s+"\n"),

  t_in: () => {return new Promise((resolve) => {
    const cb = (chunk) => resolve(chunk.trim());
    setTimeout(()=>resolve(ser({"err": "timeout"})), 2000);
    process.stdin.once("data", cb);
  })}
};
// export const delay = time => new Promise(resolve=>setTimeout(resolve,time));


export async function run_proxies() {
  const _input = proxylib.deser(process.argv[2]) || {};

  // serialize console logs with base64
  console.log = console.warn = console.info = (...args) => proxylib.t_out(proxylib.ser({"log":args}));
  console.error = (...args) => proxylib.t_out(proxylib.ser({"err":args}));

  // listen to parent instructions
  process.stdin.resume();
  process.stdin.setEncoding("ascii");

  const resp = await handler(_input);

  if (resp) {
    proxylib.t_out(proxylib.ser({ resp }))
  }

  // finalize child process:
  process.stdin.pause();
  process.exit(0);
}


run_proxies().then(()=>{

});
