/**
 * Unit tests for the AST extraction and glob matching that underpin the checker.
 * Confirms the resolver is AST-based (not regex): specifiers inside comments and
 * string literals are ignored, while real import/export/require/dynamic-import
 * specifiers are captured.
 */

import { extractSpecifiers } from '../src';
import { matchGlob } from '../src/glob';

describe('glob matcher', () => {
  it('matches source globs against posix paths', () => {
    expect(matchGlob('libs/core/src/index.ts', 'libs/**/*.ts')).toBe(true);
    expect(matchGlob('apps/api/src/app.ts', 'apps/**/*.ts')).toBe(true);
    expect(matchGlob('apps/api/src/app.ts', 'libs/**/*.ts')).toBe(false);
  });

  it('matches layer path globs including nested files', () => {
    expect(matchGlob('libs/core/src/index.ts', 'libs/core/**')).toBe(true);
    expect(matchGlob('libs/core/nested/deep/moved.ts', 'libs/core/**')).toBe(true);
    expect(matchGlob('libs/core-extra/src/x.ts', 'libs/core/**')).toBe(false);
  });
});

describe('AST specifier extraction', () => {
  it('captures real import/export/require/dynamic specifiers only', () => {
    const code = [
      "import { A } from '@afci-bench/core';",
      "export { B } from '@afci-bench/contracts';",
      "export * from '@afci-bench/observability';",
      "const c = require('@afci-bench/infra');",
      "const d = import('@afci-bench/features');",
    ].join('\n');
    const specs = extractSpecifiers('mem.ts', code).map((s) => s.specifier).sort();
    expect(specs).toEqual(
      [
        '@afci-bench/contracts',
        '@afci-bench/core',
        '@afci-bench/features',
        '@afci-bench/infra',
        '@afci-bench/observability',
      ].sort(),
    );
  });

  it('ignores import-like text in comments and string literals', () => {
    const code = [
      "// import { Repo } from '@afci-bench/infra';",
      "/* export * from '@afci-bench/infra'; */",
      'const doc = "import { Repo } from \'@afci-bench/infra\'";',
      "const tpl = `require('@afci-bench/infra')`;",
      "export const real = 1;",
    ].join('\n');
    const specs = extractSpecifiers('mem.ts', code);
    expect(specs).toEqual([]);
  });

  it('records the type-only flag and line for a real import', () => {
    const code = "\nimport type { Order } from '@afci-bench/features';\n";
    const specs = extractSpecifiers('mem.ts', code);
    expect(specs).toHaveLength(1);
    expect(specs[0].specifier).toBe('@afci-bench/features');
    expect(specs[0].typeOnly).toBe(true);
    expect(specs[0].line).toBe(2);
  });
});
