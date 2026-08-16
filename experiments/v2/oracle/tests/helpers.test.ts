/**
 * Teardown hardening for the oracle test helpers (P2).
 *
 * The independent reviews kept observing the known Windows teardown race: the
 * recursive `rmSync` in `cleanup()` intermittently answered `ENOTEMPTY` on a
 * directory that was about to become removable, failing a test whose oracle
 * assertions had already passed. `cleanup()` now passes Node's supported
 * `maxRetries`/`retryDelay` options so those transient codes are retried.
 *
 * These tests pin the hardening itself. They assert nothing about oracle
 * scoring: `cleanup()` is test infrastructure, and this change deliberately
 * leaves every scoring semantic untouched.
 */

import * as fs from 'fs';
import * as path from 'path';

import { CLEANUP_RETRY_OPTIONS, cleanup, makeTmpRoot, materializeSnapshot } from './helpers';

describe('test-helper teardown', () => {
  it('declares a retry budget for the Windows teardown race', () => {
    // Node retries EBUSY/EMFILE/ENFILE/ENOTEMPTY/EPERM only when maxRetries > 0.
    expect(CLEANUP_RETRY_OPTIONS.maxRetries).toBeGreaterThan(0);
    expect(CLEANUP_RETRY_OPTIONS.retryDelay).toBeGreaterThan(0);
  });

  it('passes the retry options through to the removal call', () => {
    // `fs.rmSync` is non-configurable in this runtime, so it cannot be spied on;
    // the helper source is checked instead. That is the assertion that matters:
    // the retry budget is useless unless it actually reaches `rmSync`.
    const source = fs.readFileSync(path.join(__dirname, 'helpers.ts'), 'utf-8');
    expect(source).toMatch(
      /fs\.rmSync\(\s*tmpRoot,\s*\{\s*recursive:\s*true,\s*force:\s*true,\s*\.\.\.CLEANUP_RETRY_OPTIONS\s*\}\s*\)/,
    );
    expect(source).toMatch(/maxRetries/);
    expect(source).toMatch(/retryDelay/);
  });

  it('removes a populated snapshot tree and is idempotent', () => {
    const tmp = makeTmpRoot();
    const snapshotDir = materializeSnapshot(tmp, 'clean_alias');
    expect(fs.existsSync(path.join(snapshotDir, 'tsconfig.json'))).toBe(true);

    cleanup(tmp);
    expect(fs.existsSync(tmp)).toBe(false);

    // `force: true` means a second teardown of an already-removed root is a
    // no-op rather than an ENOENT — teardown must never fail a passing test.
    expect(() => cleanup(tmp)).not.toThrow();
  });
});
