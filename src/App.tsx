import {
  Sparkles,
  ArrowRight,
  Bot,
  TrendingUp,
  Shield,
  ShieldCheck,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  ResponsiveContainer,
} from "recharts";

const chartData = [
  { m: "Sep", v: 18.2 },
  { m: "Oct", v: 19.4 },
  { m: "Nov", v: 20.1 },
  { m: "Dec", v: 21.6 },
  { m: "Jan", v: 22.9 },
  { m: "Feb", v: 24.85 },
];

function Header() {
  return (
    <header className="header">
      <div className="brand">
        <div className="logo-badge">B</div>
        <div className="brand-text">
          <span className="brand-name">BankNova AI</span>
          <span className="brand-sub">WEALTH OS</span>
        </div>
      </div>
      <nav className="nav-actions">
        <a href="#" className="nav-link">
          Log in
        </a>
        <a href="#" className="btn btn-primary">
          Get started
        </a>
      </nav>
    </header>
  );
}

function PortfolioCard() {
  return (
    <div className="portfolio-card">
      <div className="portfolio-top">
        <span className="portfolio-label">PORTFOLIO</span>
        <span className="portfolio-yoy">+12.4% YoY</span>
      </div>
      <div className="portfolio-value">
        <span className="rupee">₹</span>24,85,320
      </div>
      <div className="portfolio-sub">Total wealth · Feb 2026</div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={90}>
          <AreaChart data={chartData} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="goldFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f5b03e" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#f5b03e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="m" hide />
            <Area
              type="monotone"
              dataKey="v"
              stroke="#f5b03e"
              strokeWidth={2}
              fill="url(#goldFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="sub-cards">
        <div className="sub-card">
          <span className="sub-card-label">SAVINGS</span>
          <span className="sub-card-value">₹ 3.5L</span>
        </div>
        <div className="sub-card">
          <span className="sub-card-label">INVESTMENTS</span>
          <span className="sub-card-value">₹ 18.2L</span>
        </div>
        <div className="sub-card">
          <span className="sub-card-label">EMERGENCY</span>
          <span className="sub-card-value">₹ 3.1L</span>
        </div>
      </div>

      <div className="insight-card">
        <Sparkles className="insight-icon" size={16} />
        <div>
          <span className="insight-label">AI INSIGHT</span>
          <p className="insight-text">
            You're on track for retirement at 58. Bumping SIP by ₹5K lands you
            there at 55.
          </p>
        </div>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section className="hero">
      <div className="hero-copy">
        <div className="hero-badge">
          <Sparkles size={14} />
          Powered by Gemini 3 · Built for India
        </div>
        <h1 className="hero-title">
          Your <span className="gold">personal</span> wealth
          <br />
          intelligence layer.
        </h1>
        <p className="hero-desc">
          BankNova AI is a premium digital wealth OS that understands your
          money in ₹, forecasts your goals, and explains every recommendation
          like a private banker would.
        </p>
        <div className="hero-cta-row">
          <a href="#" className="btn btn-primary btn-lg">
            Open free account <ArrowRight size={16} />
          </a>
          <a href="#" className="btn btn-ghost">
            I already have an account
          </a>
        </div>
        <div className="trust-row">
          <span>
            <ShieldCheck size={14} /> Bank-grade security
          </span>
          <span>Explainable AI</span>
          <span>INR-native</span>
        </div>
      </div>
      <div className="hero-visual">
        <PortfolioCard />
      </div>
    </section>
  );
}

const features = [
  {
    icon: Bot,
    title: "AI Financial Advisor",
    desc: "Chat with a Gemini-powered advisor trained on Indian markets, taxes & personal finance.",
  },
  {
    icon: TrendingUp,
    title: "Portfolio X-Ray",
    desc: "Upload CSV. Get diversification score, risk metrics & AI rebalancing suggestions.",
  },
  {
    icon: Sparkles,
    title: "Goal Planning",
    desc: "Inflation-adjusted SIP calculators for retirement, education, home & every life goal.",
  },
  {
    icon: Shield,
    title: "Financial Health",
    desc: "7-pillar health score with explainable insights across savings, debt, insurance & more.",
  },
];

function Features() {
  return (
    <section className="features">
      {features.map((f) => (
        <div className="feature-card" key={f.title}>
          <f.icon className="feature-icon" size={22} />
          <h3 className="feature-title">{f.title}</h3>
          <p className="feature-desc">{f.desc}</p>
        </div>
      ))}
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <p className="footer-copy">
        © 2026 BankNova AI · Built for IDBI Innovate 2026
      </p>
      <p className="footer-disclaimer">
        This is a hackathon prototype — not licensed investment advice.
      </p>
      <div className="footer-badge">
        <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
          <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" strokeWidth="1.2" />
          <circle cx="8" cy="8" r="2.4" />
        </svg>
        Made with Emergent
      </div>
    </footer>
  );
}

function App() {
  return (
    <div className="page">
      <Header />
      <Hero />
      <Features />
      <Footer />
    </div>
  );
}

export default App;
