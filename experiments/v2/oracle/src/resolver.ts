/**
 * AST-based import graph resolver (TypeScript compiler API).
 *
 * Import and re-export edges are extracted from the parsed AST, never by regex,
 * so specifiers that appear only inside comments or string literals are ignored.
 * Module specifiers are resolved with ts.resolveModuleName using the snapshot's
 * own tsconfig, so path aliases, relative paths, and index/barrel resolution
 * behave as the compiler does. When an internal specifier does not resolve to a
 * file (moved/deleted target), the layer is still attributed from the alias
 * target or the normalized relative path, so a violation is not missed.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as ts from 'typescript';

import { OracleError } from './errors';
import { LayerMap } from './layers';
import { EdgeKind, ImportEdge } from './types';

function toPosix(p: string): string {
  return p.split(path.sep).join('/');
}

/** Recursively list .ts/.tsx source files under `dir` (posix, relative to `dir`). */
export function listSourceFiles(dir: string): string[] {
  const out: string[] = [];
  const skip = new Set(['node_modules', '.git', 'dist', 'coverage', '.nx']);
  const walk = (abs: string): void => {
    const entries = fs.readdirSync(abs, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name));
    for (const e of entries) {
      if (e.isDirectory()) {
        if (!skip.has(e.name)) {
          walk(path.join(abs, e.name));
        }
      } else if (e.isFile() && /\.tsx?$/.test(e.name) && !e.name.endsWith('.d.ts')) {
        out.push(toPosix(path.relative(dir, path.join(abs, e.name))));
      }
    }
  };
  walk(dir);
  return out.sort();
}

/** Parse the snapshot tsconfig; fail closed on a malformed or missing config. */
export function parseCompilerOptions(snapshotDir: string, aliasConfigPath: string): ts.CompilerOptions {
  const configAbs = path.resolve(snapshotDir, aliasConfigPath);
  if (!fs.existsSync(configAbs)) {
    throw new OracleError(
      'MISSING_EVALUATOR_FILE',
      'the snapshot alias config referenced by the manifest does not exist',
      configAbs,
    );
  }
  const text = fs.readFileSync(configAbs, 'utf-8');
  let parsed: { config?: unknown; error?: ts.Diagnostic };
  try {
    parsed = ts.parseConfigFileTextToJson(configAbs, text);
  } catch (e) {
    // Severely malformed JSON can make the parser throw rather than return .error.
    throw new OracleError('MALFORMED_ALIAS_CONFIG', 'the snapshot tsconfig could not be parsed', String(e));
  }
  if (parsed.error) {
    throw new OracleError(
      'MALFORMED_ALIAS_CONFIG',
      'the snapshot tsconfig is not valid JSON',
      ts.flattenDiagnosticMessageText(parsed.error.messageText, '\n'),
    );
  }
  const host: ts.ParseConfigHost = {
    useCaseSensitiveFileNames: ts.sys.useCaseSensitiveFileNames,
    fileExists: (f) => fs.existsSync(f),
    readFile: (f) => (fs.existsSync(f) ? fs.readFileSync(f, 'utf-8') : undefined),
    readDirectory: () => [],
  };
  const converted = ts.parseJsonConfigFileContent(parsed.config, host, path.resolve(snapshotDir));
  const options = converted.options;
  if (!options.baseUrl) {
    options.baseUrl = path.resolve(snapshotDir);
  }
  // A malformed `paths` structure surfaces as a fatal config error.
  const fatal = converted.errors.find((d) => d.category === ts.DiagnosticCategory.Error && d.code !== 18003);
  if (fatal) {
    throw new OracleError(
      'MALFORMED_ALIAS_CONFIG',
      'the snapshot tsconfig has a malformed compiler/path configuration',
      ts.flattenDiagnosticMessageText(fatal.messageText, '\n'),
    );
  }
  return options;
}

interface RawSpecifier {
  specifier: string;
  kind: EdgeKind;
  typeOnly: boolean;
  line: number;
  column: number;
}

/** Extract every static/dynamic module specifier from a source file's AST. */
export function extractSpecifiers(fileAbs: string, text: string): RawSpecifier[] {
  const sf = ts.createSourceFile(fileAbs, text, ts.ScriptTarget.Latest, /*setParentNodes*/ true, ts.ScriptKind.TS);
  const specs: RawSpecifier[] = [];
  const at = (pos: number): { line: number; column: number } => {
    const lc = sf.getLineAndCharacterOfPosition(pos);
    return { line: lc.line + 1, column: lc.character + 1 };
  };
  const push = (node: ts.Node, specifier: string, kind: EdgeKind, typeOnly: boolean): void => {
    const { line, column } = at(node.getStart(sf));
    specs.push({ specifier, kind, typeOnly, line, column });
  };
  const visit = (node: ts.Node): void => {
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
      const typeOnly = !!node.importClause && node.importClause.isTypeOnly;
      push(node, node.moduleSpecifier.text, 'import', typeOnly);
    } else if (
      ts.isExportDeclaration(node) &&
      node.moduleSpecifier &&
      ts.isStringLiteral(node.moduleSpecifier)
    ) {
      push(node, node.moduleSpecifier.text, 'export-from', node.isTypeOnly);
    } else if (
      ts.isImportEqualsDeclaration(node) &&
      ts.isExternalModuleReference(node.moduleReference) &&
      node.moduleReference.expression &&
      ts.isStringLiteral(node.moduleReference.expression)
    ) {
      push(node, node.moduleReference.expression.text, 'require', node.isTypeOnly);
    } else if (ts.isCallExpression(node)) {
      const isRequire = ts.isIdentifier(node.expression) && node.expression.text === 'require';
      const isDynamicImport = node.expression.kind === ts.SyntaxKind.ImportKeyword;
      if ((isRequire || isDynamicImport) && node.arguments.length >= 1) {
        const arg = node.arguments[0];
        // Accept both '...' string literals and `...` no-substitution template
        // literals (both are StringLiteralLike and carry a compiler-resolvable
        // specifier); a backtick require()/import() must not launder a dependency.
        if (ts.isStringLiteralLike(arg)) {
          push(node, arg.text, isDynamicImport ? 'dynamic-import' : 'require', false);
        }
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
  return specs;
}

function isInternalSpecifier(specifier: string, options: ts.CompilerOptions): boolean {
  if (specifier.startsWith('.')) {
    return true;
  }
  const paths = options.paths ?? {};
  return Object.keys(paths).some((key) => {
    if (key.endsWith('/*')) {
      return specifier.startsWith(key.slice(0, -1));
    }
    return specifier === key;
  });
}

/** Attribute a layer to an internal specifier that did not resolve to a file. */
function attributeUnresolvedLayer(
  specifier: string,
  importerAbs: string,
  snapshotDir: string,
  options: ts.CompilerOptions,
  layerMap: LayerMap,
): { rel: string | null; layer: string | null } {
  let candidate: string | null = null;
  if (specifier.startsWith('.')) {
    const abs = path.resolve(path.dirname(importerAbs), specifier);
    candidate = toPosix(path.relative(snapshotDir, abs));
  } else {
    const paths = options.paths ?? {};
    const base = options.baseUrl ?? path.resolve(snapshotDir);
    for (const [key, targets] of Object.entries(paths)) {
      if (!targets || targets.length === 0) {
        continue;
      }
      let target: string | null = null;
      if (key.endsWith('/*') && specifier.startsWith(key.slice(0, -1))) {
        const suffix = specifier.slice(key.length - 1);
        target = targets[0].replace('*', suffix);
      } else if (specifier === key) {
        target = targets[0];
      }
      if (target) {
        candidate = toPosix(path.relative(snapshotDir, path.resolve(base, target)));
        break;
      }
    }
  }
  if (!candidate) {
    return { rel: null, layer: null };
  }
  // Try the path itself and a couple of barrel-normalized variants.
  const variants = [candidate, `${candidate}/index.ts`, `${candidate}.ts`];
  for (const v of variants) {
    const layer = layerMap.layerOf(v);
    if (layer) {
      return { rel: candidate, layer };
    }
  }
  return { rel: candidate, layer: layerMap.layerOf(candidate) };
}

export class ImportGraphResolver {
  private readonly snapshotDir: string;
  private readonly options: ts.CompilerOptions;
  private readonly layerMap: LayerMap;
  private readonly host: ts.ModuleResolutionHost;

  constructor(snapshotDir: string, options: ts.CompilerOptions, layerMap: LayerMap) {
    this.snapshotDir = snapshotDir;
    this.options = options;
    this.layerMap = layerMap;
    this.host = {
      fileExists: (f) => fs.existsSync(f),
      readFile: (f) => (fs.existsSync(f) ? fs.readFileSync(f, 'utf-8') : undefined),
      directoryExists: (d) => fs.existsSync(d) && fs.statSync(d).isDirectory(),
      getCurrentDirectory: () => this.snapshotDir,
      getDirectories: (d) =>
        fs.existsSync(d)
          ? fs
              .readdirSync(d, { withFileTypes: true })
              .filter((e) => e.isDirectory())
              .map((e) => e.name)
          : [],
      realpath: (p) => {
        try {
          return fs.realpathSync(p);
        } catch {
          return p;
        }
      },
    };
  }

  /** Resolve a specifier to a posix relative path inside the snapshot, or null. */
  private resolveToRel(specifier: string, importerAbs: string): string | null {
    const res = ts.resolveModuleName(specifier, importerAbs, this.options, this.host);
    const file = res.resolvedModule?.resolvedFileName;
    if (!file) {
      return null;
    }
    const abs = path.resolve(file);
    const rel = toPosix(path.relative(this.snapshotDir, abs));
    if (rel.startsWith('..') || path.isAbsolute(rel)) {
      return null; // resolved outside the snapshot (e.g. node_modules): external
    }
    return rel;
  }

  /**
   * Follow `export {x} from '...'` / `export * from '...'` hops out of a barrel
   * for evidence enrichment (bounded depth, cycle-guarded). Does not change the
   * edge decision; it records the transitive re-export target for the chain.
   */
  private followReExports(barrelRel: string, depth: number, seen: Set<string>): string[] {
    if (depth <= 0 || seen.has(barrelRel)) {
      return [];
    }
    seen.add(barrelRel);
    const abs = path.resolve(this.snapshotDir, barrelRel);
    if (!fs.existsSync(abs)) {
      return [];
    }
    const specs = extractSpecifiers(abs, fs.readFileSync(abs, 'utf-8')).filter((s) => s.kind === 'export-from');
    const chain: string[] = [];
    for (const s of specs) {
      const rel = this.resolveToRel(s.specifier, abs);
      if (rel) {
        chain.push(`${barrelRel} re-exports from ${s.specifier} -> ${rel}`);
        chain.push(...this.followReExports(rel, depth - 1, seen));
      } else {
        chain.push(`${barrelRel} re-exports from ${s.specifier} (unresolved)`);
      }
    }
    return chain;
  }

  buildEdges(sourceFiles: string[]): ImportEdge[] {
    const edges: ImportEdge[] = [];
    for (const rel of sourceFiles) {
      const abs = path.resolve(this.snapshotDir, rel);
      const importerLayer = this.layerMap.layerOf(rel);
      const text = fs.readFileSync(abs, 'utf-8');
      for (const spec of extractSpecifiers(abs, text)) {
        const internal = isInternalSpecifier(spec.specifier, this.options);
        const resolvedRel = this.resolveToRel(spec.specifier, abs);
        let targetPath: string | null = null;
        let targetLayer: string | null = null;
        let internalUnresolved = false;
        const chain: string[] = [];

        if (resolvedRel) {
          targetPath = resolvedRel;
          targetLayer = this.layerMap.layerOf(resolvedRel);
          chain.push(`${spec.kind} '${spec.specifier}' -> ${resolvedRel}`);
          if (/(^|\/)index\.tsx?$/.test(resolvedRel)) {
            chain.push(...this.followReExports(resolvedRel, 5, new Set<string>()));
          }
        } else if (internal) {
          internalUnresolved = true;
          const attr = attributeUnresolvedLayer(spec.specifier, abs, this.snapshotDir, this.options, this.layerMap);
          targetLayer = attr.layer;
          chain.push(`${spec.kind} '${spec.specifier}' unresolved (moved/deleted target); layer attributed by path -> ${attr.layer ?? 'unknown'}`);
        } else {
          // third-party / ungoverned; not an internal architecture edge
          continue;
        }

        // Only internal edges (target within a governed layer or internal-unresolved) matter.
        if (targetLayer === null && !internalUnresolved) {
          continue;
        }

        edges.push({
          importer_path: rel,
          importer_layer: importerLayer,
          specifier: spec.specifier,
          kind: spec.kind,
          type_only: spec.typeOnly,
          line: spec.line,
          column: spec.column,
          target_path: targetPath,
          target_layer: targetLayer,
          internal_unresolved: internalUnresolved,
          resolution_chain: chain,
        });
      }
    }
    // Deterministic ordering.
    edges.sort(
      (a, b) =>
        a.importer_path.localeCompare(b.importer_path) ||
        a.line - b.line ||
        a.column - b.column ||
        a.specifier.localeCompare(b.specifier),
    );
    return edges;
  }
}
