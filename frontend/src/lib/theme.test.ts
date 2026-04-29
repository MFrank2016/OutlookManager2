import test from "node:test";
import assert from "node:assert/strict";

import { getNextTheme, getThemeToggleLabel } from "./theme.ts";

test("getNextTheme: dark -> light", () => {
  assert.equal(getNextTheme("dark"), "light");
});

test("getNextTheme: light -> dark", () => {
  assert.equal(getNextTheme("light"), "dark");
});

test("getNextTheme: undefined -> dark", () => {
  assert.equal(getNextTheme(undefined), "dark");
});

test("getThemeToggleLabel: dark -> 切换到浅色主题", () => {
  assert.equal(getThemeToggleLabel("dark"), "切换到浅色主题");
});

test("getThemeToggleLabel: light -> 切换到深色主题", () => {
  assert.equal(getThemeToggleLabel("light"), "切换到深色主题");
});

test("getThemeToggleLabel: undefined -> 切换到深色主题", () => {
  assert.equal(getThemeToggleLabel(undefined), "切换到深色主题");
});
