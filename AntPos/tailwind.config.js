const plugin = require('tailwindcss/plugin')

module.exports = {
  presets: [require('frappe-ui/src/utils/tailwind.config')],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // antPOS surface scale. Structure comes from these hairlines rather than
        // shadows -- a counter screen is usually viewed at a glancing angle,
        // where stacked shadows just muddy the edges.
        pos: {
          page: '#F4F5F7',
          line: '#E3E6EA',
          line2: '#CFD5DD',
          ink: '#12161C',
          ink2: '#5A6472',
          ink3: '#8B95A3',
          readout: '#171C24',
          pay: '#0B7A4B',
          'pay-hover': '#09693F',
          ret: '#C2410C',
          warn: '#B45309',
        },
      },
    },
  },
  plugins: [
    plugin(({ addUtilities }) => {
      addUtilities({
        '.scrollbar-hide::-webkit-scrollbar': {
          display: 'none',
        },
        '.scrollbar-hide': {
          '-ms-overflow-style': 'none', /* IE and Edge */
          'scrollbar-width': 'none', /* Firefox */
        },
      })
    }),
  ],
}
