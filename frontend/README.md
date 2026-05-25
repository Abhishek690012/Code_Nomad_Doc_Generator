# ⚡ Codewise Frontend

This is the frontend client for the Codewise AI Documentation Generator, built with React and Vite.

## 📋 Requirements

- **Node.js** 18+
- **npm** 9+

### Key Dependencies
- `react` ^18.3.1
- `react-dom` ^18.3.1
- `vite` ^7.3.3 (dev)

## ⚙️ Environment Variables

Create a `.env` file in the frontend root:
```env
VITE_API_URL=http://localhost:5000
```
Change `VITE_API_URL` to your production backend URL (e.g. deployed on Render) when deploying.

## 🚀 How to Run

### Development
```bash
npm install
npm run dev
```

### Production Build
```bash
npm run build
```
This builds static files into `dist/`.

## 🌐 Deploy to Netlify
- **Build command:** `npm run build`
- **Publish directory:** `dist`
- **Environment variables:** Add `VITE_API_URL` pointing to your live Flask backend.
