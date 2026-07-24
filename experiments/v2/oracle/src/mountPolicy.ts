/**
 * Evaluator-mount boundary enforcement (docs/v2/EVALUATOR_MOUNT_POLICY.md §2/§3).
 *
 * The frozen evaluator manifest MUST be mounted OUTSIDE the coding worktree. Both
 * paths are resolved to real (symlink-free) absolute paths before the containment
 * check, so a symlink cannot smuggle the mount inside the worktree. A mount
 * inside the worktree is a fail-closed refusal (INFRA_EVALUATOR_MOUNT).
 */

import * as fs from 'fs';
import * as path from 'path';

import { OracleError } from './errors';

/** Realpath the longest existing prefix and re-append the missing remainder. */
function realpathBestEffort(target: string): string {
  let current = path.resolve(target);
  const tail: string[] = [];
  // Walk up until an existing ancestor is found, then realpath it.
  // Guard against an infinite loop at the filesystem root.
  for (let guard = 0; guard < 4096; guard += 1) {
    if (fs.existsSync(current)) {
      const real = fs.realpathSync(current);
      return tail.length ? path.join(real, ...tail.reverse()) : real;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }
    tail.push(path.basename(current));
    current = parent;
  }
  return path.resolve(target);
}

/** True when `child` is `parent` itself or nested inside `parent`. */
export function isInside(parent: string, child: string): boolean {
  const rel = path.relative(parent, child);
  if (rel === '') {
    return true;
  }
  return !rel.startsWith('..') && !path.isAbsolute(rel);
}

/**
 * Throw OracleError(INFRA_EVALUATOR_MOUNT) if `manifestPath` resolves to a path
 * inside `snapshotDir`. Returns the resolved (real) snapshot and manifest paths.
 */
export function assertEvaluatorMountOutsideWorktree(
  snapshotDir: string,
  manifestPath: string,
): { snapshotReal: string; manifestReal: string } {
  const snapshotReal = realpathBestEffort(snapshotDir);
  const manifestReal = realpathBestEffort(manifestPath);
  if (isInside(snapshotReal, manifestReal)) {
    throw new OracleError(
      'INFRA_EVALUATOR_MOUNT',
      'evaluator manifest is mounted inside the coding worktree; it must be mounted outside',
      `snapshot=${snapshotReal} manifest=${manifestReal}`,
    );
  }
  return { snapshotReal, manifestReal };
}
