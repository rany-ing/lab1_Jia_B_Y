import { Link } from 'react-router-dom'
import { extractNewsPreview, formatDate } from '../utils/format'
import styles from './NewsCard.module.css'

export default function NewsCard({ news, authorName }) {
  const preview = extractNewsPreview(news.content)

  return (
    <article className={styles.card}>
      {news.cover && (
        <Link to={`/news/${news.id}`} className={styles.coverWrap}>
          <img src={news.cover} alt={news.title} className={styles.cover} />
        </Link>
      )}
      <div className={styles.body}>
        <div className={styles.meta}>
          <span>{authorName || `Автор #${news.author_id}`}</span>
          <span>•</span>
          <time dateTime={news.published_at}>{formatDate(news.published_at)}</time>
        </div>
        <h2 className={styles.title}>
          <Link to={`/news/${news.id}`} className={styles.titleLink}>
            {news.title}
          </Link>
        </h2>
        {preview && <p className={styles.preview}>{preview}</p>}
        <Link to={`/news/${news.id}`} className={styles.readMore}>
          Читать далее →
        </Link>
      </div>
    </article>
  )
}
