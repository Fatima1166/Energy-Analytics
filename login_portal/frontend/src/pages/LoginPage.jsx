import { useState } from 'react'
import {
  Lock,
  Mail,
  KeyRound,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Zap,
  Sun,
  Leaf,
} from 'lucide-react'
import axios from 'axios'

const IMAGES = {
  logo: 'https://flagcdn.com/w160/pk.png',
  hero: '/login_hero.jpg',
}

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.')
      return
    }

    setLoading(true)

    try {
      const res = await axios.post('/api/login', {
        username: username.trim(),
        password,
      })

      if (res.data.success) {
        onLogin()
      } else {
        setError(res.data.message || 'Invalid credentials. Please try again.')
      }
    } catch (err) {
      if (err.response && err.response.data) {
        setError(err.response.data.message || 'Login failed. Please try again.')
      } else {
        setError('Could not connect to server. Please check your connection.')
      }
    } finally {
      setLoading(false)
    }
  }

  const features = [
    {
      num: '01',
      title: 'Energy Supply',
      desc: 'Track primary and secondary energy sources',
      icon: <Zap size={16} />,
    },
    {
      num: '02',
      title: 'Renewable Impact',
      desc: 'Monitor clean energy growth and share',
      icon: <Sun size={16} />,
    },
    {
      num: '03',
      title: 'Sustainability',
      desc: 'Build a cleaner, greener Pakistan',
      icon: <Leaf size={16} />,
    },
  ]

  return (
    <div className="login-container">
      {/* ======================== LEFT HERO ======================== */}
      <section className="hero-panel">
        <img
          src={IMAGES.hero}
          alt="Pakistan Energy Infrastructure"
          className="hero-image"
        />
        <div className="hero-overlay" />

        <div className="hero-content">
          {/* Logo */}
          <div className="hero-logo-lockup">
            <div className="hero-logo-wrap">
              <img src={IMAGES.logo} alt="Pakistan Flag" />
            </div>
            <span className="hero-brand-title">Pakistan Energy</span>
          </div>

          {/* Main Content */}
          <div className="hero-main-content">
            <h1 className="hero-title">
              Outlook &amp; Renewable
              <br />
              Impact Dashboard
            </h1>
            <p className="hero-subtitle">
              Data-driven insights for a sustainable energy future. Monitor,
              analyze, and transform Pakistan&apos;s energy landscape.
            </p>

            {/* Feature List */}
            <div className="feature-list">
              {features.map((f, i) => (
                <div
                  key={f.num}
                  className="feature-item"
                  style={{ '--delay': `${i * 0.15}s` }}
                >
                  <div className="feature-number">{f.num}</div>
                  <div className="feature-text">
                    <strong>{f.title}</strong>
                    <small>{f.desc}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom */}
          <div className="hero-bottom">
            <div className="hero-bottom-line" />
            <strong>Powering a cleaner, greener Pakistan</strong>
            <span>Insight today. Impact tomorrow.</span>
          </div>
        </div>
      </section>

      {/* ======================== RIGHT LOGIN ======================== */}
      <section className="login-panel">
        {/* Floating Particles */}
        <div className="particle particle-1" />
        <div className="particle particle-2" />
        <div className="particle particle-3" />

        <div className="login-card">
          <div className="login-card-inner">
            {/* Icon */}
            <div className="login-icon-wrap">
              <Lock size={28} />
            </div>

            {/* Title */}
            <h2 className="login-form-title">Welcome Back</h2>
            <p className="login-form-subtitle">
              Sign in to access the Pakistan Energy
              <br />
              Outlook &amp; Renewable Impact Dashboard
            </p>

            {/* Error */}
            {error && (
              <div className="error-message">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} id="login-form" autoComplete="off">
              {/* Username */}
              <div className="input-group">
                <label htmlFor="login-username">Username</label>
                <div className="input-wrapper">
                  <Mail className="input-icon" size={18} />
                  <input
                    id="login-username"
                    type="text"
                    placeholder="Enter your username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoComplete="username"
                    disabled={loading}
                  />
                </div>
              </div>

              {/* Password */}
              <div className="input-group">
                <label htmlFor="login-password">Password</label>
                <div className="input-wrapper">
                  <KeyRound className="input-icon" size={18} />
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    disabled={loading}
                  />
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                className="login-btn"
                id="login-submit"
                disabled={loading}
              >
                {loading ? (
                  <div className="spinner" />
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight size={18} className="btn-arrow" />
                  </>
                )}
              </button>
            </form>

            {/* Security Badge */}
            <div className="security-badge">
              <span className="security-dot" />
              Protected access · bcrypt encrypted credentials
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
