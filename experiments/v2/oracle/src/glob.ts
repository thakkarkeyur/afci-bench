/**
 * Minimal, dependency-free glob matcher for posix-style relative paths.
 *
 * Supports the subset the oracle needs: `**` (any characters, including path
 * separators), `*` (any characters except a separator), and `?` (a single
 * non-separator character). All other characters are matched literally. Used for
 * source-file selection and for frozen layer path globs, so no npm glob
 * dependency is added to the frozen lockfile.
 */

function escapeRegExp(literal: string): string {
  return literal.replace(/[.+^${}()|[\]\\]/g, '\\$&');
}

/** Compile a single glob to an anchored RegExp over posix paths. */
export function globToRegExp(glob: string): RegExp {
  let re = '';
  for (let i = 0; i < glob.length; i += 1) {
    const ch = glob[i];
    if (ch === '*') {
      if (glob[i + 1] === '*') {
        // `**` — any characters including separators.
        re += '.*';
        i += 1;
        // Swallow a trailing slash after `**` so `a/**` also matches `a`.
        if (glob[i + 1] === '/') {
          re += '(?:/)?';
          i += 1;
        }
      } else {
        // `*` — any characters except a separator.
        re += '[^/]*';
      }
    } else if (ch === '?') {
      re += '[^/]';
    } else {
      re += escapeRegExp(ch);
    }
  }
  return new RegExp(`^${re}$`);
}

export function matchGlob(relPath: string, glob: string): boolean {
  return globToRegExp(glob).test(relPath);
}

export function matchAnyGlob(relPath: string, globs: string[]): boolean {
  return globs.some((g) => matchGlob(relPath, g));
}
