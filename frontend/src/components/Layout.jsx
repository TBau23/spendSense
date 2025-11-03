import { Link, Outlet } from 'react-router-dom';
import './Layout.css';

function Layout() {
  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-content">
          <Link to="/" className="nav-brand">
            SpendSense
          </Link>
          <div className="nav-links">
            <Link to="/dashboard">Dashboard</Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="nav-link-external"
            >
              API Docs
            </a>
          </div>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="footer">
        <p>
          SpendSense Demo • This is educational content, not financial advice •{' '}
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default Layout;

