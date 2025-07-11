import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);


import imagemin from 'imagemin';
import imageminPngquant from 'imagemin-pngquant';
import fs from 'fs';
import path from 'path';


// Folder to search recursively
const SCREENSHOTS_DIR = path.resolve(__dirname, 'obs_bookmark_saves');

// Compression settings
const QUALITY = [0.4, 0.6]; // adjust to make smaller/lossier if needed

async function compressScreenshot(filePath) {
  const dir = path.dirname(filePath);
  const filename = path.basename(filePath);

  const result = await imagemin([filePath], {
    destination: dir,
    plugins: [
      imageminPngquant({
        quality: QUALITY
      })
    ]
  });

  if (result.length > 0) {
    console.log(`✅ Compressed: ${filePath}`);
  } else {
    console.log(`⚠️ Failed to compress: ${filePath}`);
  }
}

function findScreenshots(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      findScreenshots(fullPath); // recurse
    } else if (entry.isFile() && entry.name === 'screenshot.png') {
      compressScreenshot(fullPath);
    }
  }
}

findScreenshots(SCREENSHOTS_DIR);
