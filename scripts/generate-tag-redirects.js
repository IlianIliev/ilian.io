// Old permalinks put tags at /tags/<slug>/; the site now serves them at
// /tag/<slug>/. GitHub Pages has no server-side rewrite rules, so for every
// tag Hugo actually built under public/tag/, drop a matching static
// redirect stub under public/tags/<slug>/ — this keeps working automatically
// as tags are added or removed, with no manual list to maintain.
const fs = require("fs");
const path = require("path");

const siteBaseURL = "https://ilian.io";
const publicDir = path.join(__dirname, "..", "public");
const tagDir = path.join(publicDir, "tag");
const legacyTagDir = path.join(publicDir, "tags");

if (!fs.existsSync(tagDir)) {
  console.error(`generate-tag-redirects: ${tagDir} not found, skipping`);
  process.exit(0);
}

const slugs = fs
  .readdirSync(tagDir, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);

for (const slug of slugs) {
  const target = `${siteBaseURL}/tag/${slug}/`;
  const stubDir = path.join(legacyTagDir, slug);
  const stubFile = path.join(stubDir, "index.html");
  const html = `<!doctype html><html lang="en-us"><head><title>${target}</title><link rel="canonical" href="${target}"><meta name="robots" content="noindex"><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=${target}"></head></html>\n`;

  fs.mkdirSync(stubDir, { recursive: true });
  fs.writeFileSync(stubFile, html);
}

console.log(`generate-tag-redirects: wrote ${slugs.length} redirect stub(s) under public/tags/`);
