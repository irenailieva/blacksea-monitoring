import { useState, FormEvent } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import useAuth from '../store/useAuth';
import { Lock, Mail } from 'lucide-react';
import logoSrc from '../assets/logo.svg';

// Компонент за страница "Вход в системата" (Login)
export default function Login() {
    // Локални състояния за формуляра
    const [email, setEmail] = useState(''); // Може да бъде имейл или потребителско име
    const [password, setPassword] = useState(''); // Парола
    const [isSubmitting, setIsSubmitting] = useState(false); // Индикатор за протичаща заявка
    
    // Вземане на метода за вход и евентуалната грешка от глобалното състояние (Zustand)
    const { loginWithCredentials, error: authError } = useAuth();
    
    const navigate = useNavigate(); // Хук за програмна навигация
    const location = useLocation(); // Хук за получаване на текущото местоположение (URL)

    // Определяне на маршрута, към който да пренасочим след успешен вход.
    // Ако потребителят се е опитал да достъпи защитена страница (напр. /dashboard) без да е логнат,
    // location.state ще съдържа { from: { pathname: '/dashboard' } }.
    const from = (location.state as any)?.from?.pathname || '/';

    // Функция, обработваща изпращането на формуляра
    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault(); // Предотвратява стандартното презареждане на страницата
        setIsSubmitting(true);

        // FastAPI OAuth2 ендпойнтът (OAuth2PasswordRequestForm) очаква данните във формат 'multipart/form-data' 
        // или 'application/x-www-form-urlencoded' със задължителни полета username и password.
        const formData = new FormData();
        formData.append('username', email); // Въпреки че променливата е email, бекендът очаква ключ 'username'
        formData.append('password', password);

        try {
            // Извикване на екшъна от Zustand store-а, който комуникира с бекенда
            await loginWithCredentials(formData);
            
            // При успех, пренасочваме потребителя към желаната страница
            // replace: true замества текущия запис в историята, така че бутонът "Назад" няма да върне на страницата за вход
            navigate(from, { replace: true });
        } catch (err) {
            // Грешката се обработва и запазва вътрешно в store (в authError),
            // затова тук не е необходимо да правим нищо.
        } finally {
            setIsSubmitting(false); // Сваляне на флага за изчакване
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-100 to-sky-100 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden border border-blue-100">
                <div className="p-8">
                    {/* Заглавна част с лого (иконка) */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4">
                            <img src={logoSrc} alt="Black Sea Monitor" className="w-16 h-16" />
                        </div>
                        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Welcome</h2>
                        <p className="text-slate-500 mt-2">Sign in to the monitoring system</p>
                    </div>

                    {/* Визуализация на грешка при неуспешен вход */}
                    {authError && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm text-center">
                            {authError}
                        </div>
                    )}

                    {/* Формуляр за вход */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Поле за потребителско име / Имейл */}
                        <div className="space-y-1">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Mail className="h-5 w-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                </div>
                                <input
                                    type="text"
                                    name="email"
                                    required
                                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-900 placeholder:text-slate-400"
                                    placeholder="Email or Username"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Поле за парола */}
                        <div className="space-y-1">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                </div>
                                <input
                                    type="password"
                                    name="password"
                                    required
                                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-900 placeholder:text-slate-400"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Бутон за изпращане */}
                        <button
                            type="submit"
                            disabled={isSubmitting} // Бутонът е деактивиран, докато се изпълнява заявката
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                        >
                            {isSubmitting ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>

                    {/* Линк към страницата за регистрация */}
                    <div className="mt-8 text-center border-t border-slate-100 pt-6">
                        <p className="text-sm text-slate-500">
                            Don't have an account?{' '}
                            <Link to="/register" className="font-semibold text-blue-600 hover:text-blue-700 transition-colors">
                                Create an account
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
