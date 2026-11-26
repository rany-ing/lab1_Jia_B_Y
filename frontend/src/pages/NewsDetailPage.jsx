import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { createComment, deleteComment, updateComment } from '../api/comments'
import { deleteNews, getNews, listNewsComments } from '../api/news'
import { listUsers } from '../api/users'
import CommentItem from '../components/CommentItem'
import { useAuth } from '../context/AuthContext'
import { formatDate } from '../utils/format'
import styles from './NewsDetailPage.module.css'

function renderContent(content) {
  if (!content) return null
  if (typeof content === 'string') {
    return <p className={styles.paragraph}>{content}</p>
  }
  if (Array.isArray(content)) {
    return (
      <div className={styles.sections}>
        {content.map((item, idx) => (
          <div key={idx} className={styles.sectionBlock}>
            {typeof item === 'string' ? <p>{item}</p> : <pre className={styles.json}>{JSON.stringify(item, null, 2)}</pre>}
          </div>
        ))}
      </div>
    )
  }

  const text = content.lead || content.text || content.body
  const sections = Array.isArray(content.sections) ? content.sections : null

  if (text || sections) {
    return (
      <div className={styles.sections}>
        {text && <p className={styles.paragraph}>{text}</p>}
        {sections?.map((sec, idx) => (
          <div key={idx} className={styles.sectionBlock}>
            {sec.heading && <h3 className={styles.sectionHeading}>{sec.heading}</h3>}
            {sec.body && <p className={styles.paragraph}>{sec.body}</p>}
          </div>
        ))}
      </div>
    )
  }

  return <pre className={styles.json}>{JSON.stringify(content, null, 2)}</pre>
}

export default function NewsDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated, isAdmin } = useAuth()

  const [news, setNews] = useState(null)
  const [comments, setComments] = useState([])
  const [usersMap, setUsersMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [commentText, setCommentText] = useState('')
  const [commentSubmitting, setCommentSubmitting] = useState(false)
  const [commentError, setCommentError] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [newsData, commentsData, users] = await Promise.all([
        getNews(id),
        listNewsComments(id),
        isAuthenticated ? listUsers().catch(() => []) : Promise.resolve([]),
      ])
      const map = {}
      for (const u of users) {
        map[u.id] = u.name
      }
      setUsersMap(map)
      setNews(newsData)
      setComments(commentsData)
    } catch (err) {
      setError(err.message || 'Не удалось загрузить новость')
    } finally {
      setLoading(false)
    }
  }, [id, isAuthenticated])

  useEffect(() => {
    loadData()
  }, [loadData])

  const canEditNews = Boolean(user && news && (user.id === news.author_id || isAdmin))

  const handleDeleteNews = async () => {
    if (!window.confirm('Удалить эту новость и все её комментарии?')) return
    try {
      await deleteNews(news.id)
      navigate('/')
    } catch (err) {
      setError(err.message || 'Не удалось удалить новость')
    }
  }

  const handleAddComment = async (e) => {
    e.preventDefault()
    if (!commentText.trim()) return
    setCommentSubmitting(true)
    setCommentError('')
    try {
      const created = await createComment({ news_id: id, text: commentText.trim() })
      setComments((prev) => [...prev, created])
      setCommentText('')
    } catch (err) {
      setCommentError(err.message || 'Не удалось добавить комментарий')
    } finally {
      setCommentSubmitting(false)
    }
  }

  const handleUpdateComment = async (commentId, text) => {
    const updated = await updateComment(commentId, text)
    setComments((prev) => prev.map((c) => (c.id === commentId ? updated : c)))
  }

  const handleDeleteComment = async (commentId) => {
    await deleteComment(commentId)
    setComments((prev) => prev.filter((c) => c.id !== commentId))
  }

  if (loading) {
    return <p className={styles.state}>Загрузка новости...</p>
  }

  if (error) {
    return (
      <div className={styles.errorBox}>
        <p>{error}</p>
        <Link to="/" className={styles.backLink}>
          ← Вернуться к новостям
        </Link>
      </div>
    )
  }

  if (!news) return null

  return (
    <article className={styles.page}>
      <Link to="/" className={styles.backLink}>
        ← Назад к ленте
      </Link>

      <div className={styles.articleCard}>
        {news.cover && <img src={news.cover} alt={news.title} className={styles.cover} />}

        <div className={styles.articleBody}>
          <div className={styles.metaRow}>
            <div className={styles.meta}>
              <span>{usersMap[news.author_id] || `Автор #${news.author_id}`}</span>
              <span>•</span>
              <time dateTime={news.published_at}>{formatDate(news.published_at)}</time>
            </div>

            {canEditNews && (
              <div className={styles.newsActions}>
                <Link to={`/news/${news.id}/edit`} className={styles.editBtn}>
                  Редактировать
                </Link>
                <button type="button" onClick={handleDeleteNews} className={styles.deleteBtn}>
                  Удалить
                </button>
              </div>
            )}
          </div>

          <h1 className={styles.title}>{news.title}</h1>
          <div className={styles.content}>{renderContent(news.content)}</div>
        </div>
      </div>

      <section className={styles.commentsSection}>
        <h2 className={styles.commentsTitle}>Комментарии ({comments.length})</h2>

        {isAuthenticated ? (
          <form onSubmit={handleAddComment} className={styles.commentForm}>
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="Напишите комментарий..."
              rows={3}
              className={styles.textarea}
              required
            />
            {commentError && <p className={styles.formError}>{commentError}</p>}
            <button type="submit" disabled={commentSubmitting} className={styles.submitBtn}>
              {commentSubmitting ? 'Отправка...' : 'Отправить комментарий'}
            </button>
          </form>
        ) : (
          <div className={styles.loginPrompt}>
            <span>Чтобы оставить комментарий, нужно </span>
            <Link to="/login">войти в аккаунт</Link>.
          </div>
        )}

        {comments.length === 0 ? (
          <p className={styles.emptyComments}>Комментариев пока нет.</p>
        ) : (
          <div className={styles.commentsList}>
            {comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                authorName={usersMap[comment.author_id]}
                onUpdate={handleUpdateComment}
                onDelete={handleDeleteComment}
              />
            ))}
          </div>
        )}
      </section>
    </article>
  )
}
