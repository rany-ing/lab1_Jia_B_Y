import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getGithubLoginUrl } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  const { login, register, isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      if (mode === 'login') {
        await login(email.trim(), password)
      } else {
        await register({ name: name.trim(), email: email.trim(), password })
      }
      navigate('/')
    } catch (err) {
      setError(err.message || 'Ошибка авторизации')
    } finally {
      setSubmitting(false)
    }
  }

  if (isAuthenticated && user) {
    return (
      <section className={styles.card}>
        <h1 className={styles.title}>Вы уже авторизованы</h1>
        <p className={styles.subtitle}>
          Текущий пользователь: <strong>{user.name}</strong> ({user.email})
        </p>
        <div className={styles.loggedActions}>
          <button type="button" onClick={() => navigate('/')} className={styles.submitBtn}>
            К новостям
          </button>
          <button type="button" onClick={logout} className={styles.secondaryBtn}>
            Выйти
          </button>
        </div>
      </section>
    )
  }

  return (
    <section className={styles.card}>
      <div className={styles.tabs}>
        <button
          type="button"
          className={`${styles.tab} ${mode === 'login' ? styles.activeTab : ''}`}
          onClick={() => {
            setMode('login')
            setError('')
          }}
        >
          Вход
        </button>
        <button
          type="button"
          className={`${styles.tab} ${mode === 'register' ? styles.activeTab : ''}`}
          onClick={() => {
            setMode('register')
            setError('')
          }}
        >
          Регистрация
        </button>
      </div>

      <h1 className={styles.title}>{mode === 'login' ? 'Вход в аккаунт' : 'Создать аккаунт'}</h1>

      {error && <div className={styles.error}>{error}</div>}

      <form onSubmit={handleSubmit} className={styles.form}>
        {mode === 'register' && (
          <label className={styles.field}>
            <span>Имя</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Иван Иванов"
              required
            />
          </label>
        )}

        <label className={styles.field}>
          <span>Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            required
          />
        </label>

        <label className={styles.field}>
          <span>Пароль</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Минимум 8 символов"
            minLength={mode === 'register' ? 8 : 1}
            required
          />
        </label>

        <button type="submit" disabled={submitting} className={styles.submitBtn}>
          {submitting
            ? 'Отправка...'
            : mode === 'login'
              ? 'Войти'
              : 'Зарегистрироваться'}
        </button>
      </form>

      <div className={styles.divider}>
        <span>или</span>
      </div>

      <a href={getGithubLoginUrl()} className={styles.githubBtn}>
        Войти через GitHub
      </a>
    </section>
  )
}
