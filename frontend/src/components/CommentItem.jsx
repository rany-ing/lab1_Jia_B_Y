import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { formatDate } from '../utils/format'
import styles from './CommentItem.module.css'

export default function CommentItem({ comment, authorName, onUpdate, onDelete }) {
  const { user, isAdmin } = useAuth()
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(comment.text)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const canManage = Boolean(user && (user.id === comment.author_id || isAdmin))

  const handleSave = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setSaving(true)
    setError('')
    try {
      await onUpdate(comment.id, text.trim())
      setEditing(false)
    } catch (err) {
      setError(err.message || 'Не удалось обновить комментарий')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm('Удалить комментарий?')) return
    setSaving(true)
    setError('')
    try {
      await onDelete(comment.id)
    } catch (err) {
      setError(err.message || 'Не удалось удалить комментарий')
      setSaving(false)
    }
  }

  return (
    <div className={styles.item}>
      <div className={styles.header}>
        <div className={styles.meta}>
          <strong className={styles.author}>{authorName || `Пользователь #${comment.author_id}`}</strong>
          <time className={styles.date} dateTime={comment.published_at}>
            {formatDate(comment.published_at)}
          </time>
        </div>

        {canManage && !editing && (
          <div className={styles.actions}>
            <button type="button" onClick={() => setEditing(true)} className={styles.actionBtn}>
              Редактировать
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={saving}
              className={`${styles.actionBtn} ${styles.deleteBtn}`}
            >
              Удалить
            </button>
          </div>
        )}
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {editing ? (
        <form onSubmit={handleSave} className={styles.editForm}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            className={styles.textarea}
            required
          />
          <div className={styles.editActions}>
            <button type="submit" disabled={saving} className={styles.saveBtn}>
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button
              type="button"
              onClick={() => {
                setEditing(false)
                setText(comment.text)
                setError('')
              }}
              className={styles.cancelBtn}
            >
              Отмена
            </button>
          </div>
        </form>
      ) : (
        <p className={styles.text}>{comment.text}</p>
      )}
    </div>
  )
}
