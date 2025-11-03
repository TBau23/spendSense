# SpendSense Frontend

React-based operator dashboard for the SpendSense financial education platform.

## Tech Stack

- React 19
- Vite
- React Router v7
- Axios for API calls

## Setup

1. **Install dependencies:**
```bash
npm install
```

2. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` if your backend runs on a different port:
```
VITE_API_BASE_URL=http://localhost:8000
```

3. **Start development server:**
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Project Structure

```
src/
├── api/
│   ├── client.js          # Axios instance with interceptors
│   └── services.js        # API service functions
├── components/
│   ├── Layout.jsx         # Main layout with navbar/footer
│   └── Layout.css
├── pages/
│   ├── Home.jsx           # Landing page
│   ├── Dashboard.jsx      # User list view
│   └── UserDetail.jsx     # Individual user view
├── App.jsx                # Router configuration
├── main.jsx               # Entry point
└── index.css              # Global styles
```

## Available Routes

- `/` - Home page
- `/dashboard` - Operator dashboard (user list)
- `/user/:userId` - User detail view with signals and recommendations

## API Integration

The app expects the FastAPI backend to be running on `http://localhost:8000`.

API endpoints used:
- `GET /health` - Health check
- `GET /users` - List all users
- `GET /profile/{user_id}` - Get user profile with persona
- `GET /signals/{user_id}` - Get behavioral signals
- `GET /recommendations/{user_id}` - Get recommendations
- `GET /consent/{user_id}` - Check consent status
- `POST /consent` - Record consent
- `DELETE /consent/{user_id}` - Revoke consent

## Development

- Hot Module Replacement (HMR) is enabled by default
- ESLint is configured for code quality
- Run linter: `npm run lint`
- Build for production: `npm run build`
- Preview production build: `npm run preview`

## Next Steps

1. Complete backend API implementation
2. Generate synthetic user data
3. Implement signal detection and persona assignment
4. Build recommendation engine
5. Add consent management UI
6. Create data visualization components for signals
