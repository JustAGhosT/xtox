module.exports = [
  require('@eslint/js').configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'module',
      globals: {
        ...require('globals').browser,
        ...require('globals').node,
        ...require('globals').es2021,
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      react: require('eslint-plugin-react'),
      'jsx-a11y': require('eslint-plugin-jsx-a11y'),
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      ...require('eslint-plugin-react').configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off', // Disable prop-types for now (using TypeScript-style props)
      'jsx-a11y/anchor-is-valid': 'warn',
      'jsx-a11y/click-events-have-key-events': 'warn',
      'jsx-a11y/no-static-element-interactions': 'warn',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  },
  {
    ignores: [
      'build/**',
      'node_modules/**',
      '*.config.js',
      '**/xtotext Tailwind Configuration.js', // Design token reference file
    ],
  },
];

