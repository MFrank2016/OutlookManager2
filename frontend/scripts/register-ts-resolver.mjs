/**
 * 让 node --test --experimental-strip-types 能解析省略 .ts 扩展名的相对导入。
 * 不改 tsconfig，因为这里只修复 node:test 运行时解析，不影响 TypeScript 编译基线。
 * 仅服务 frontend 的测试入口。
 */
import { register } from "node:module";

register(new URL("./ts-resolver-hooks.mjs", import.meta.url), import.meta.url);
