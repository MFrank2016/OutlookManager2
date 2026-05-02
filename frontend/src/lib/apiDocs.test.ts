import test from "node:test";
import assert from "node:assert/strict";

import {
  appendRequestHistory,
  buildBodyPayloadFromFieldValues,
  extractMessageCandidates,
  filterJsonValue,
  buildRequestUrl,
  matchesOperationScope,
  parseOpenApiSpec,
  pickDefaultOperation,
  toggleFavoriteOperation,
} from "./apiDocs";

test("parseOpenApiSpec should flatten OpenAPI paths into searchable operations", () => {
  const spec = {
    openapi: "3.1.0",
    paths: {
      "/auth/login": {
        post: {
          tags: ["认证"],
          summary: "登录",
          description: "管理员登录",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    username: { type: "string", default: "admin" },
                    password: { type: "string" },
                  },
                },
              },
            },
          },
        },
      },
      "/accounts/{email_id}": {
        delete: {
          tags: ["账户管理"],
          summary: "删除账户",
          parameters: [
            {
              name: "email_id",
              in: "path",
              required: true,
              schema: { type: "string" },
            },
          ],
        },
      },
    },
  };

  const operations = parseOpenApiSpec(spec);

  assert.equal(operations.length, 2);
  assert.deepEqual(
    operations.map((item) => `${item.method} ${item.path}`),
    ["POST /auth/login", "DELETE /accounts/{email_id}"],
  );
  assert.equal(operations[0]?.tag, "认证");
  assert.equal((operations[0]?.bodyTemplate as Record<string, unknown>)?.username, "admin");
  assert.equal(operations[1]?.parameters[0]?.name, "email_id");
});

test("buildRequestUrl should interpolate path params and append query params", () => {
  const url = buildRequestUrl("/accounts/{email_id}/messages", {
    email_id: "demo@example.com",
  }, {
    page: "2",
    page_size: "50",
    empty: "",
  });

  assert.equal(
    url,
    "/accounts/demo%40example.com/messages?page=2&page_size=50",
  );
});

test("pickDefaultOperation should prioritize health and auth endpoints over public share routes", () => {
  const operations = parseOpenApiSpec({
    openapi: "3.1.0",
    paths: {
      "/share/{token}/emails": {
        get: {
          tags: ["分享码"],
          summary: "公开邮件列表",
        },
      },
      "/auth/login": {
        post: {
          tags: ["认证"],
          summary: "登录",
        },
      },
      "/api": {
        get: {
          summary: "API状态检查",
        },
      },
    },
  });

  const selected = pickDefaultOperation(operations);
  assert.equal(selected?.id, "GET /api");
});

test("matchesOperationScope should filter public, auth and v2 operations correctly", () => {
  const operations = parseOpenApiSpec({
    openapi: "3.1.0",
    paths: {
      "/share/{token}/emails": {
        get: {
          tags: ["分享码"],
          summary: "公开邮件列表",
        },
      },
      "/api/v2/accounts": {
        post: {
          tags: ["API v2 / 账户"],
          summary: "注册账户",
          security: [{ HTTPBearer: [] }],
        },
      },
    },
  });

  const publicOp = operations.find((item) => item.id === "GET /share/{token}/emails");
  const v2Op = operations.find((item) => item.id === "POST /api/v2/accounts");

  assert.equal(matchesOperationScope(publicOp!, "public"), true);
  assert.equal(matchesOperationScope(publicOp!, "auth"), false);
  assert.equal(matchesOperationScope(v2Op!, "auth"), true);
  assert.equal(matchesOperationScope(v2Op!, "v2"), true);
});

test("toggleFavoriteOperation should add and remove the same operation id", () => {
  const added = toggleFavoriteOperation(["GET /api"], "POST /auth/login");
  assert.deepEqual(added, ["GET /api", "POST /auth/login"]);

  const removed = toggleFavoriteOperation(added, "GET /api");
  assert.deepEqual(removed, ["POST /auth/login"]);
});

test("appendRequestHistory should prepend latest request and cap the list length", () => {
  const history = appendRequestHistory(
    [
      {
        id: "older",
        operationId: "GET /old",
        method: "GET",
        path: "/old",
        requestUrl: "/old",
        status: 200,
        ok: true,
        durationMs: 12,
        requestedAt: "2026-05-02T00:00:00.000Z",
        responsePreview: "older",
        stateSnapshot: {
          pathValues: {},
          queryValues: {},
          headerValues: {},
          bodyValue: "",
          extraHeadersJson: "{}",
          manualToken: "",
          useStoredToken: true,
        },
      },
    ],
    {
      id: "latest",
      operationId: "GET /api",
      method: "GET",
      path: "/api",
      requestUrl: "/api",
      status: 200,
      ok: true,
      durationMs: 8,
      requestedAt: "2026-05-02T01:00:00.000Z",
      responsePreview: "service ok",
      stateSnapshot: {
        pathValues: {},
        queryValues: {},
        headerValues: {},
        bodyValue: "",
        extraHeadersJson: "{}",
        manualToken: "",
        useStoredToken: true,
      },
    },
    1,
  );

  assert.equal(history.length, 1);
  assert.equal(history[0]?.id, "latest");
});

test("parseOpenApiSpec should build visual body field definitions for object payloads", () => {
  const operations = parseOpenApiSpec({
    openapi: "3.1.0",
    paths: {
      "/auth/login": {
        post: {
          summary: "登录",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  required: ["username", "password"],
                  properties: {
                    username: { type: "string", description: "用户名" },
                    password: { type: "string", description: "密码" },
                    metadata: {
                      type: "object",
                      properties: {
                        source: { type: "string" },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
  });

  const login = operations[0]!;
  assert.equal(login.bodyFields.length, 3);
  assert.equal(login.bodyFields[0]?.required, true);
  assert.equal(login.bodyFields[2]?.editor, "json");
});

test("buildBodyPayloadFromFieldValues should validate required fields and parse json field values", () => {
  const result = buildBodyPayloadFromFieldValues(
    [
      {
        key: "username",
        label: "username",
        type: "string",
        required: true,
        defaultValue: "",
        editor: "text",
      },
      {
        key: "metadata",
        label: "metadata",
        type: "object",
        required: true,
        defaultValue: {},
        editor: "json",
      },
    ],
    {
      username: "admin",
      metadata: "{\"source\":\"api-docs\"}",
    },
  );

  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.payload, {
    username: "admin",
    metadata: { source: "api-docs" },
  });
});

test("filterJsonValue should keep only matching branches for search", () => {
  const filtered = filterJsonValue(
    {
      message: "ok",
      nested: {
        target_value: "hello",
        ignored: "world",
      },
    },
    "target",
  );

  assert.deepEqual(filtered, {
    nested: {
      target_value: "hello",
    },
  });
});

test("extractMessageCandidates should normalize message list payloads", () => {
  const candidates = extractMessageCandidates({
    emails: [
      {
        message_id: "INBOX-1",
        subject: "Welcome",
        from_email: "hello@example.com",
        date: "2026-05-02T00:00:00",
      },
    ],
  });

  assert.equal(candidates.length, 1);
  assert.equal(candidates[0]?.messageId, "INBOX-1");
  assert.equal(candidates[0]?.subject, "Welcome");
});
