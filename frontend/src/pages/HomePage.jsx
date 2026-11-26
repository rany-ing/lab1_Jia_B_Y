import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listNews } from '../api/news'
import { listUsers } from '../api/users'
import NewsCard from '../components/NewsCard'
import { useAuth } from '../context/AuthContext'
import styles from './HomePage.module.css'

export default function HomePage() {
  const { isAuthenticated, canPublishNews } = useAuth()
  const [newsList, setNewsList] = useState([])
  const [usersMap, setUsersMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [requiresAuth, setRequiresAuth] = useState(false)

  useEffect(() => {
    let active = true

    async function fetchData() {
      setLoading(true)
      setError('')
      setRequiresAuth(false)
      try {
        const [items, users] = await Promise.all([
          listNews(),
          isAuthenticated ? listUsers().catch(() => []) : Promise.resolve([]),
        ])
        if (!active) return
        const map = {}
        for (const u of users) {
          map[u.id] = u.name
        }
        setUsersMap(map)
        setNewsList(items)
      } catch (err) {
        if (!active) return
        if (err.status === 401) {
          setRequiresAuth(true)
        } else {
          setError(err.message || 'Не удалось загрузить новости')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    fetchData()
    return () => {
      active = false
    }
  }, [isAuthenticated])

  return (
    <section className={styles.page}>
      <div className={styles.headerRow}>
        <div>
          <h1 className={styles.heading}>Лента новостей</h1>
          <p className={styles.subheading}>Актуальные публикации и обсуждения</p>
        </div>
        {canPublishNews && (
          <Link to="/news/new" className={styles.createBtn}>
            + Создать новость
          </Link>
        )}
      </div>

      {loading && <p className={styles.state}>Загрузка новостей...</p>}

      {!loading && requiresAuth && (
        <div className={styles.authPrompt}>
          <p>Для просмотра ленты новостей на этом сервере требуется авторизация.</p>
          <Link to="/login" className={styles.loginLink}>
            Перейти ко входу
          </Link>
        </div>
      )}

      {!loading && error && <div className={styles.error}>{error}</div>}

      {!loading && !error && !requiresAuth && newsList.length === 0 && (
        <p className={styles.state}>Новостей пока нет.</p>
      )}

      {!loading && !error && !requiresAuth && newsList.length > 0 && (
        <div className={styles.grid}>
          {newsList.map((item) => (
            <NewsCard key={item.id} news={item} authorName={usersMap[item.author_id]} />
          ))}
        </div>
      )}
    </section>
  )
}
