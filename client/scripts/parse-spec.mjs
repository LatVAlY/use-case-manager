import { readFileSync } from 'fs';

const spec = JSON.parse(readFileSync('/vercel/share/v0-project/lib/openapi-spec.json', 'utf-8'));

console.log("=== PATHS ===");
for (const [path, methods] of Object.entries(spec.paths)) {
  for (const [method, details] of Object.entries(methods)) {
    console.log(`\n${method.toUpperCase()} ${path}`);
    console.log(`  Summary: ${details.summary}`);
    console.log(`  Tags: ${details.tags?.join(', ')}`);
    console.log(`  OperationId: ${details.operationId}`);
    if (details.security) console.log(`  Auth Required: YES`);
    if (details.requestBody) {
      const contentTypes = Object.keys(details.requestBody.content);
      console.log(`  Content-Type: ${contentTypes.join(', ')}`);
      for (const ct of contentTypes) {
        const schema = details.requestBody.content[ct].schema;
        if (schema?.$ref) console.log(`  Body Schema: ${schema.$ref}`);
        else console.log(`  Body Schema: ${JSON.stringify(schema)}`);
      }
    }
    if (details.parameters) {
      console.log(`  Parameters: ${JSON.stringify(details.parameters)}`);
    }
  }
}

console.log("\n\n=== SCHEMAS ===");
for (const [name, schema] of Object.entries(spec.components.schemas)) {
  console.log(`\n${name}:`);
  if (schema.properties) {
    for (const [prop, propDef] of Object.entries(schema.properties)) {
      const required = schema.required?.includes(prop) ? ' (REQUIRED)' : '';
      const type = propDef.type || propDef.$ref || (propDef.anyOf ? propDef.anyOf.map(a => a.type || a.$ref).join(' | ') : 'unknown');
      const defaultVal = propDef.default !== undefined ? ` default=${JSON.stringify(propDef.default)}` : '';
      const titleStr = propDef.title ? ` [${propDef.title}]` : '';
      console.log(`  ${prop}: ${type}${required}${defaultVal}${titleStr}`);
    }
  }
  if (schema.enum) console.log(`  enum: ${JSON.stringify(schema.enum)}`);
}
