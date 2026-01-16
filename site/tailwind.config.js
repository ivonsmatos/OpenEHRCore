/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            colors: {
                primary: {
                    50: '#f0f9ff',
                    100: '#e0f2fe',
                    500: '#0ea5e9', // Sky 500
                    600: '#0284c7', // Sky 600
                    700: '#0369a1', // Sky 700
                    800: '#075985', // Sky 800
                    900: '#0c4a6e', // Sky 900
                },
                accent: {
                    500: '#14b8a6', // Teal 500
                    600: '#0d9488', // Teal 600
                }
            }
        },
    },
    plugins: [],
}
