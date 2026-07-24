// Standalone Jest config for the architecture-conformance oracle.
//
// The oracle lives outside the nx workspace (experiments/), so it is NOT part of
// `npm run test`/`npm run ci`. It is run explicitly via `npm run oracle:test`
// (jest -c experiments/v2/oracle/jest.config.js). Plain CommonJS so `tsc`
// (root typecheck) ignores this file.
module.exports = {
  displayName: 'afci-oracle',
  rootDir: __dirname,
  testEnvironment: 'node',
  transform: {
    '^.+\\.ts$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.json', diagnostics: true }],
  },
  testMatch: ['<rootDir>/tests/**/*.test.ts'],
  moduleFileExtensions: ['ts', 'js', 'json'],
  // Fixtures are .ts.fixture templates materialized at test time; never collected.
  testPathIgnorePatterns: ['/node_modules/', '/fixtures/'],
};
