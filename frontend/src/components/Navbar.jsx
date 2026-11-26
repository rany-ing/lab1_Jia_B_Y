import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Navbar.module.css'

export default function Navbar() {
  const { user, isAuthenticated, canPublishNews, isAdmin, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.left}>
          <Link to="/" className={styles.brand}>
            News Portal
          </Link>
          <nav className={styles.nav}>
            <Link to="/" className={styles.navLink}>
              Новости
            </Link>
            {canPublishNews && (
              <Link to="/news/new" className={styles.createBtn}>
                + Создать новость
              </Link>
            )}
          </nav>
        </div>

        <div className={styles.right}>
          {isAuthenticated && user ? (
            <div className={styles.userBox}>
              <div className={styles.userInfo}>
                <span className={styles.userName}>{user.name}</span>
                <div className={styles.badges}>
                  {isAdmin && <span className={`${styles.badge} ${styles.badgeAdmin}`}>Админ</span>}
                  {user.is_verified_author && (
                    <span className={`${styles.badge} ${styles.badgeVerified}`}>Автор</span>
                  )}
                  {!isAdmin && !user.is_verified_author && (
                    <span className={`${styles.badge} ${styles.badgeReader}`}>Читатель</span>
                  )}
                </div>
              </div>
              <button type="button" onClick={handleLogout} className={styles.logoutBtn}>
                Выйти
              </button>
            </div>
          ) : (
            <Link to="/login" className={styles.loginBtn}>
              Войти
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
