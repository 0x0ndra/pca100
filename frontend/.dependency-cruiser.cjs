/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: 'lib-no-components-or-hooks',
      comment: 'lib is pure/shared; it must not depend on components or hooks',
      severity: 'error',
      from: { path: '^src/lib' },
      to: { path: '^src/(components|hooks)' },
    },
    {
      name: 'components-no-direct-api',
      comment: 'components never call the API client directly; hooks do',
      severity: 'error',
      from: { path: '^src/components' },
      to: { path: '^src/lib/api' },
    },
  ],
  options: {
    tsConfig: {
      fileName: 'tsconfig.app.json',
    },
  },
}
