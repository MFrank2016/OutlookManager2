export async function resolve(specifier, context, nextResolve) {
  try {
    return await nextResolve(specifier, context);
  } catch (error) {
    if (
      error &&
      error.code === "ERR_MODULE_NOT_FOUND" &&
      /^\.{1,2}\/?/.test(specifier) &&
      !specifier.endsWith(".ts")
    ) {
      return nextResolve(`${specifier}.ts`, context);
    }
    throw error;
  }
}
