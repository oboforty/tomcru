import proxylib from "aws-sdk/proxylib";
import { handler } from "./index.js";


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
