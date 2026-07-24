/**
 * Out-of-band CLI for the architecture-conformance oracle.
 *
 * Runs the oracle over a final repository snapshot using a frozen, externally
 * mounted manifest and prints the raw architecture_finding JSON. It is an
 * EVALUATOR, run only after model generation ends; it invokes no model. Exit
 * codes: 0 CONFORMANT, 2 VIOLATIONS, 3 fail-closed (OracleError), 4 PENDING
 * (an applicable rule is unimplemented), 1 unexpected error.
 *
 * Usage:
 *   ts-node experiments/v2/oracle/src/cli.ts \
 *     --snapshot <dir> --manifest <path outside snapshot> [--out finding.json] [--snapshot-id id]
 */

import * as fs from 'fs';

import { evaluateSnapshot } from './engine';
import { OracleError } from './errors';

interface Args {
  snapshot?: string;
  manifest?: string;
  out?: string;
  snapshotId?: string;
}

function parseArgs(argv: string[]): Args {
  const args: Args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const next = (): string => argv[(i += 1)];
    if (a === '--snapshot') args.snapshot = next();
    else if (a === '--manifest') args.manifest = next();
    else if (a === '--out') args.out = next();
    else if (a === '--snapshot-id') args.snapshotId = next();
  }
  return args;
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));
  if (!args.snapshot || !args.manifest) {
    process.stderr.write('usage: --snapshot <dir> --manifest <path> [--out file] [--snapshot-id id]\n');
    return 1;
  }
  try {
    const finding = evaluateSnapshot({
      snapshotDir: args.snapshot,
      manifestPath: args.manifest,
      snapshotId: args.snapshotId,
      scoredAt: null,
    });
    const json = JSON.stringify(finding, null, 2);
    if (args.out) {
      fs.writeFileSync(args.out, json, 'utf-8');
    }
    process.stdout.write(`${json}\n`);
    if (finding.verdict === 'VIOLATIONS') return 2;
    if (finding.verdict === 'PENDING') return 4;
    return 0;
  } catch (e) {
    if (e instanceof OracleError) {
      process.stderr.write(`ORACLE_FAIL_CLOSED ${e.reason}: ${e.message}\n`);
      return 3;
    }
    process.stderr.write(`UNEXPECTED_ERROR: ${String(e)}\n`);
    return 1;
  }
}

// Use process.exitCode (not process.exit) so buffered stdout is flushed before exit.
process.exitCode = main();
