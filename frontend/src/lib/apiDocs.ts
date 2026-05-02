export interface OpenApiParameter {
  name: string;
  in: "path" | "query" | "header" | "cookie";
  required?: boolean;
  description?: string;
  schema?: Record<string, unknown>;
  example?: unknown;
}

function isOpenApiParameter(value: unknown): value is OpenApiParameter {
  return (
    isRecord(value) &&
    typeof value.name === "string" &&
    (value.in === "path" || value.in === "query" || value.in === "header" || value.in === "cookie")
  );
}

export interface ApiDocOperation {
  id: string;
  method: string;
  path: string;
  tag: string;
  summary: string;
  description: string;
  parameters: OpenApiParameter[];
  requiresAuth: boolean;
  bodyRequired: boolean;
  bodyTemplate: Record<string, unknown> | unknown[] | string | number | boolean | null;
}

export type ApiDocScope = "all" | "v2" | "auth" | "public";

type OpenApiSpec = {
  openapi?: string;
  components?: {
    schemas?: Record<string, Record<string, unknown>>;
  };
  paths?: Record<string, Record<string, Record<string, unknown>>>;
};

const HTTP_METHODS = new Set(["get", "post", "put", "delete", "patch"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function resolveSchemaRef(spec: OpenApiSpec, schema: unknown): unknown {
  if (!isRecord(schema)) return schema;
  const ref = schema.$ref;
  if (typeof ref !== "string") return schema;
  const schemaName = ref.split("/").pop();
  if (!schemaName) return schema;
  return spec.components?.schemas?.[schemaName] ?? schema;
}

function buildTemplateFromSchema(
  spec: OpenApiSpec,
  schema: unknown,
  seen = new Set<string>()
): Record<string, unknown> | unknown[] | string | number | boolean | null {
  const resolved = resolveSchemaRef(spec, schema);
  if (!isRecord(resolved)) {
    return null;
  }

  const ref = typeof resolved.$ref === "string" ? resolved.$ref : null;
  if (ref) {
    if (seen.has(ref)) return null;
    const nextSeen = new Set(seen);
    nextSeen.add(ref);
    return buildTemplateFromSchema(spec, resolveSchemaRef(spec, resolved), nextSeen);
  }

  if ("example" in resolved) {
    return (resolved.example as Record<string, unknown>) ?? null;
  }
  if ("default" in resolved) {
    return (resolved.default as Record<string, unknown>) ?? null;
  }
  if (Array.isArray(resolved.enum) && resolved.enum.length > 0) {
    return resolved.enum[0] as string | number | boolean | null;
  }

  if (Array.isArray(resolved.oneOf) && resolved.oneOf.length > 0) {
    return buildTemplateFromSchema(spec, resolved.oneOf[0], seen);
  }
  if (Array.isArray(resolved.anyOf) && resolved.anyOf.length > 0) {
    return buildTemplateFromSchema(spec, resolved.anyOf[0], seen);
  }
  if (Array.isArray(resolved.allOf) && resolved.allOf.length > 0) {
    return resolved.allOf.reduce<Record<string, unknown>>((acc, item) => {
      const partial = buildTemplateFromSchema(spec, item, seen);
      if (isRecord(partial)) {
        Object.assign(acc, partial);
      }
      return acc;
    }, {});
  }

  const type = resolved.type;
  if (type === "object" || resolved.properties) {
    const properties = isRecord(resolved.properties) ? resolved.properties : {};
    const output: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(properties)) {
      output[key] = buildTemplateFromSchema(spec, value, seen);
    }
    return output;
  }

  if (type === "array") {
    return [];
  }
  if (type === "boolean") {
    return false;
  }
  if (type === "integer" || type === "number") {
    return 0;
  }
  if (type === "string") {
    return "";
  }
  return null;
}

export function parseOpenApiSpec(spec: OpenApiSpec): ApiDocOperation[] {
  const operations: ApiDocOperation[] = [];

  for (const [path, candidates] of Object.entries(spec.paths ?? {})) {
    for (const [method, operation] of Object.entries(candidates)) {
      if (!HTTP_METHODS.has(method.toLowerCase()) || !isRecord(operation)) {
        continue;
      }

      const tags = Array.isArray(operation.tags) ? operation.tags : [];
      const parameters = Array.isArray(operation.parameters)
        ? operation.parameters.filter(isOpenApiParameter)
        : [];
      const requestBody = isRecord(operation.requestBody) ? operation.requestBody : null;
      const jsonBodySchema = requestBody?.content &&
        isRecord(requestBody.content) &&
        isRecord(requestBody.content["application/json"])
        ? (requestBody.content["application/json"] as Record<string, unknown>).schema
        : null;

      operations.push({
        id: `${method.toUpperCase()} ${path}`,
        method: method.toUpperCase(),
        path,
        tag: typeof tags[0] === "string" ? tags[0] : "未分组",
        summary: typeof operation.summary === "string" ? operation.summary : path,
        description: typeof operation.description === "string" ? operation.description : "",
        parameters,
        requiresAuth: Array.isArray(operation.security) && operation.security.length > 0,
        bodyRequired: Boolean(requestBody?.required),
        bodyTemplate: jsonBodySchema ? buildTemplateFromSchema(spec, jsonBodySchema) : null,
      });
    }
  }

  return operations.sort((a, b) => {
    if (a.tag !== b.tag) return a.tag.localeCompare(b.tag, "zh-CN");
    if (a.path !== b.path) return a.path.localeCompare(b.path, "zh-CN");
    return a.method.localeCompare(b.method, "zh-CN");
  });
}

export function matchesOperationScope(operation: ApiDocOperation, scope: ApiDocScope): boolean {
  switch (scope) {
    case "v2":
      return operation.path.startsWith("/api/v2");
    case "auth":
      return operation.requiresAuth;
    case "public":
      return !operation.requiresAuth;
    case "all":
    default:
      return true;
  }
}

export function pickDefaultOperation(operations: ApiDocOperation[]): ApiDocOperation | null {
  const priorityMatchers = [
    (item: ApiDocOperation) => item.method === "GET" && item.path === "/api",
    (item: ApiDocOperation) => item.method === "POST" && item.path === "/auth/login",
    (item: ApiDocOperation) => item.method === "GET" && item.path === "/auth/me",
    (item: ApiDocOperation) => item.path.startsWith("/api/v2"),
    (item: ApiDocOperation) => item.path.startsWith("/accounts"),
    (item: ApiDocOperation) => !item.requiresAuth,
  ];

  for (const matches of priorityMatchers) {
    const found = operations.find(matches);
    if (found) {
      return found;
    }
  }

  return operations[0] ?? null;
}

export function buildRequestUrl(
  path: string,
  pathParams: Record<string, string>,
  queryParams: Record<string, string>
): string {
  let url = path;

  for (const [key, value] of Object.entries(pathParams)) {
    url = url.replace(`{${key}}`, encodeURIComponent(value));
  }

  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(queryParams)) {
    if (value !== "") {
      query.set(key, value);
    }
  }

  const queryString = query.toString();
  return queryString ? `${url}?${queryString}` : url;
}
