import { Link } from 'react-router-dom';
import './Home.css';

function Home() {
  return (
    <div className="home">
      <div className="hero">
        <h1>SpendSense</h1>
        <p className="tagline">From Plaid to Personalized Learning</p>
        <p className="description">
          Behavioral pattern detection and personalized financial education
          with strict compliance guardrails
        </p>
      </div>

      <div className="features">
        <div className="feature-card">
          <h3>Behavioral Signals</h3>
          <p>Detect subscriptions, savings patterns, credit utilization, and income stability</p>
        </div>
        <div className="feature-card">
          <h3>Smart Personas</h3>
          <p>Assign users to personas based on financial behaviors and priorities</p>
        </div>
        <div className="feature-card">
          <h3>Educational Content</h3>
          <p>Personalized recommendations with clear rationales and data citations</p>
        </div>
        <div className="feature-card">
          <h3>Compliance First</h3>
          <p>Consent tracking, eligibility checks, and tone validation built-in</p>
        </div>
      </div>

      <div className="cta">
        <Link to="/dashboard" className="btn-primary">
          Open Operator Dashboard
        </Link>
      </div>
    </div>
  );
}

export default Home;

