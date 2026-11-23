import {get, put} from '@vercel/blob';
import {readFileSync} from 'node:fs';

const path = 'voice-control/rules.sqlite3';
const [operation, etag] = process.argv.slice(2);
if (operation === 'read') {
  const result = await get(path, {access:'private', useCache:false});
  if (result === null) {
    console.log(JSON.stringify({}));
  } else {
    if (result.statusCode !== 200) throw new Error('Cannot load stored rules');
    const bytes = Buffer.from(await new Response(result.stream).arrayBuffer());
    console.log(JSON.stringify({etag:result.blob.etag, data:bytes.toString('base64')}));
  }
} else if (operation === 'write') {
  const result = await put(path, readFileSync(0), {access:'private', addRandomSuffix:false,
    allowOverwrite:Boolean(etag), ...(etag ? {ifMatch:etag} : {})});
  console.log(JSON.stringify({etag:result.etag}));
}
