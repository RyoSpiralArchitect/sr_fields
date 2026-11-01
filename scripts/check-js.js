import { readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const directory = fileURLToPath(new URL('../app/', import.meta.url));
for (const file of readdirSync(directory).filter(name => name.endsWith('.js'))) {
  const result = spawnSync(process.execPath, ['--check', `${directory}/${file}`], {stdio: 'inherit'});
  if (result.status !== 0) process.exit(1);
}
console.log('All browser modules passed syntax checks.');
