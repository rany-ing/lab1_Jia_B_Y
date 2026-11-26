import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { createNews, getNews, updateNews } from '../api/news'
import { useAuth } from '../context/AuthContext'
import { extractNewsPreview } from '../utils/format'
import styles from './NewsFormPage.module.css'

export default function NewsFormPage() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const { user, canPublishNews, isAdmin, loading: authLoading } = useAuth()

  const [title, setTitle] = useState('')
  const [cover, setCover] = useState('')
  const [contentText, setContentText] = useState('')
  const [loading, setLoading] = useState(isEdit)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [forbidden, setForbidden] = useState(false)

  useEffect(() => {
    if (!isEdit || authLoading) return
    let active = true

    async function fetchNews() {
      try {
        const data = await getNews(id)
        if (!active) return
        if (!user || (user.id !== data.author_id && !isAdmin)) {
          setForbidden(true)
          return
        }
        setTitle(data.title)
        setCover(data.cover || '')
        setContentText(extractNewsPreview(data.content))
      } catch (err) {
        if (active) setError(err.message || 'Не удалось загрузить новость')
      } finally {
        if (active) setLoading(false)
      }
    }

    fetchNews()
    return () => {
      active = false
    }
  }, [id, isEdit, user, isAdmin, authLoading])

  if (authLoading || loading) {
    return <p className={styles.state}>Загрузка...</p>
  }

  if (!isEdit && !canPublishNews) {
    return (
      <div className={styles.blocked}>
        <p>Создавать новости могут только верифицированные авторы и администраторы.</p>
        <Link to="/" className={styles.backLink}>
          ← Вернуться к новостям
        </Link>
      </div>
    )
  }

  if (forbidden) {
    return (
      <div className={styles.blocked}>
        <p>У вас нет прав на редактирование этой новости.</p>
        <Link to={`/news/${id}`} className={styles.backLink}>
          ← Назад к новости
        </Link>
      </div>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        title: title.trim(),
        content: { text: contentText.trim() },
        cover: cover.trim() || null,
      }
      if (isEdit) {
        await updateNews(id, payload)
        navigate(`/news/${id}`)
      } else {
        const created = await createNews(payload)
        navigate(`/news/${created.id}`)
      }
    } catch (err) {
      setError(err.message || 'Ошибка сохранения новости')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className={styles.card}>
      <Link to={isEdit ? `/news/${id}` : '/'} className={styles.backLink}>
        ← Назад
      </Link>
      <h1 className={styles.title}>{isEdit ? 'Редактировать новость' : 'Создать новость'}</h1>

      {error && <div className={styles.error}>{error}</div>}

      <form onSubmit={handleSubmit} className={styles.form}>
        <label className={styles.field}>
          <span>Заголовок</span>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Введите заголовок новости"
            maxLength={255}
            required
          />
        </label>

        <label className={styles.field}>
          <span>Обложка (URL, необязательно)</span>
          <input
            type="url"
            value={cover}
            onChange={(e) => setCover(e.target.value)}
            placeholder="https://example.com/cover.jpg"
            maxLength={500}
          />
        </label>

        <label className={styles.field}>
          <span>Контент</span>
          <textarea
            value={contentText}
            onChange={(e) => setContentText(e.target.value)}
            placeholder="Текст новости..."
            rows={8}
            required
          />
        </label>

        <button type="submit" disabled={submitting} className={styles.submitBtn}>
          {submitting ? 'Сохранение...' : isEdit ? 'Сохранить изменения' : 'Опубликовать'}
        </button>
      </form>
    </section>
  )
}
