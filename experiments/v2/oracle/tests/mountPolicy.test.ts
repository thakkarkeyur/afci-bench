/**
 * Machine-checkable proof that an evaluator mount inside the coding worktree is
 * rejected (docs/v2/EVALUATOR_MOUNT_POLICY.md §2/§3), and that a legal sibling
 * mount is accepted.
 */

import * as path from 'path';

import { evaluateSnapshot, assertEvaluatorMountOutsideWorktree, isInside, OracleError } from '../src';
import { baseManifest, cleanup, makeTmpRoot, materializeSnapshot, writeManifest } from './helpers';

describe('evaluator mount policy', () => {
  it('rejects a manifest mounted inside the coding worktree', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = materializeSnapshot(tmp, 'clean_alias');
      // Mount the manifest INSIDE the snapshot (illegal).
      const manifestPath = writeManifest(tmp, baseManifest(), 'snapshot/evaluator');
      let thrown: unknown;
      try {
        evaluateSnapshot({ snapshotDir, manifestPath });
      } catch (e) {
        thrown = e;
      }
      expect(thrown).toBeInstanceOf(OracleError);
      expect((thrown as OracleError).reason).toBe('INFRA_EVALUATOR_MOUNT');
    } finally {
      cleanup(tmp);
    }
  });

  it('accepts a manifest mounted in a sibling directory outside the worktree', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = materializeSnapshot(tmp, 'clean_alias');
      const manifestPath = writeManifest(tmp, baseManifest(), 'evaluator');
      expect(() =>
        assertEvaluatorMountOutsideWorktree(snapshotDir, manifestPath),
      ).not.toThrow();
      // And a full evaluation runs without a mount error.
      const r = evaluateSnapshot({ snapshotDir, manifestPath });
      expect(r.verdict).toBe('CONFORMANT');
    } finally {
      cleanup(tmp);
    }
  });

  it('isInside detects nesting and equality but not siblings', () => {
    const parent = path.resolve('/tmp/wt');
    expect(isInside(parent, path.resolve('/tmp/wt'))).toBe(true);
    expect(isInside(parent, path.resolve('/tmp/wt/evaluator/m.json'))).toBe(true);
    expect(isInside(parent, path.resolve('/tmp/evaluator/m.json'))).toBe(false);
    expect(isInside(parent, path.resolve('/tmp/wt-sibling/m.json'))).toBe(false);
  });
});
