import test from "node:test";
import assert from "node:assert/strict";

import { buildRequestUrl, parseOpenApiSpec } from "./apiDocs";

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
