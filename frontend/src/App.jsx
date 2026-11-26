import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import { AuthProvider } from './context/AuthContext'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import NewsDetailPage from './pages/NewsDetailPage'
import NewsFormPage from './pages/NewsFormPage'
import styles from './App.module.css'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className={styles.layout}>
          <Navbar />
          <main className={styles.main}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/news/new" element={<NewsFormPage />} />
              <Route path="/news/:id" element={<NewsDetailPage />} />
              <Route path="/news/:id/edit" element={<NewsFormPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  )
}
