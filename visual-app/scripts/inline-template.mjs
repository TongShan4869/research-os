import { readFile, readdir, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(scriptDir, "..");
const repoDir = resolve(appDir, "..");
const distDir = join(appDir, "dist");
const assetsDir = join(distDir, "assets");
const outputPath = join(repoDir, "src", "research_os", "visual_template.html");

const assets = await readdir(assetsDir);
const jsAsset = assets.find((asset) => asset.endsWith(".js"));
const cssAsset = assets.find((asset) => asset.endsWith(".css"));

if (!jsAsset || !cssAsset) {
  throw new Error("Expected Vite to emit one JS asset and one CSS asset.");
}

let html = await readFile(join(distDir, "index.html"), "utf8");
const js = (await readFile(join(assetsDir, jsAsset), "utf8")).replaceAll("</script", "<\\/script");
const css = (await readFile(join(assetsDir, cssAsset), "utf8")).replaceAll("</style", "<\\/style");

html = html
  .replace(/<link rel="stylesheet" crossorigin href="\/assets\/[^"]+">/, () => `<style>\n${css}\n</style>`)
  .replace(/<script type="module" crossorigin src="\/assets\/[^"]+"><\/script>/, () => `<script type="module">\n${js}\n</script>`)
  .replace(
    /<script id="research-os-graph-data" type="application\/json">[\s\S]*?<\/script>/,
    '<script id="research-os-graph-data" type="application/json">__RESEARCH_OS_GRAPH_DATA__</script>',
  );

await writeFile(outputPath, html, "utf8");
console.log(`wrote ${outputPath}`);
