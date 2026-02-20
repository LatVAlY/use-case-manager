import { readFileSync } from 'fs';

const raw = readFileSync('/vercel/share/v0-project/lib/openapi-spec.json', 'utf-8');
const spec = JSON.parse(raw);

console.log("=== TITLE ===");
console.log(JSON.stringify(spec.info, null, 2));

console.log("\n=== PATHS ===");
for (const [path, methods] of Object.entries(spec.paths || {})) {
  for (const [method, detail] of Object.entries(methods)) {
    console.log(`\n${method.toUpperCase()} ${path}`);
    console.log(`  Summary: ${detail.summary || 'N/A'}`);
    console.log(`  OperationId: ${detail.operationId || 'N/A'}`);
    if (detail.parameters) {
      console.log(`  Parameters: ${JSON.stringify(detail.parameters)}`);
    }
    if (detail.requestBody) {
      console.log(`  RequestBody: ${JSON.stringify(detail.requestBody)}`);
    }
    if (detail.responses) {
      for (const [code, resp] of Object.entries(detail.responses)) {
        console.log(`  Response ${code}: ${JSON.stringify(resp)}`);
      }
    }
  }
}

console.log("\n=== SCHEMAS ===");
if (spec.components && spec.components.schemas) {
  for (const [name, schema] of Object.entries(spec.components.schemas)) {
    console.log(`\n${name}: ${JSON.stringify(schema, null, 2)}`);
  }
}
