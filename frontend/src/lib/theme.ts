export type ResolvedTheme = "light" | "dark";

export function getNextTheme(resolvedTheme: string | undefined): ResolvedTheme {
  return resolvedTheme === "dark" ? "light" : "dark";
}

export function getThemeToggleLabel(resolvedTheme: string | undefined): string {
  return getNextTheme(resolvedTheme) === "light" ? "切换到浅色主题" : "切换到深色主题";
}
