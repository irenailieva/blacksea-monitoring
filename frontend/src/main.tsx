import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

// Намираме главния DOM елемент ('root'), където ще бъде рендирано цялото React приложение
const rootElement = document.getElementById('root');

// Проверяваме дали елементът съществува, за да избегнем TypeScript/JavaScript грешки
if (rootElement) {
  // Създаваме корен (root) на React 18+ и извикваме render метода
  createRoot(rootElement).render(
    // StrictMode е инструмент за откриване на потенциални проблеми в приложението.
    // Той не визуализира видим потребителски интерфейс, а активира допълнителни проверки и предупреждения.
    <StrictMode>
      {/* Рендираме главния компонент на приложението, съдържащ цялата логика и маршрутизация */}
      <App />
    </StrictMode>,
  )
}
