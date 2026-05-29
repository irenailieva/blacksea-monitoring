import { useState, ChangeEvent, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuth from '../store/useAuth';
import { Waves, Lock, User, Mail } from 'lucide-react';

// Компонент за страница "Регистрация" (Register)
export default function Register() {
    // Обектно състояние за всички полета от регистрационния формуляр
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    
    // Състояния за съобщения към потребителя
    const [error, setError] = useState(''); // Съобщение при грешка
    const [successMsg, setSuccessMsg] = useState(''); // Съобщение при успешна регистрация
    
    // Вземане на метода за регистрация от глобалния auth store
    const { register } = useAuth();
    const navigate = useNavigate();

    // Универсален обработчик за промени в input полетата
    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        // Динамично обновяване на конкретното поле по неговия атрибут `name`
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    // Обработчик за изпращане на регистрационния формуляр
    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault(); // Спиране на презареждането на страницата
        setError('');

        // Валидация на клиентска страна: проверка дали двете пароли съвпадат
        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        try {
            // Изпращане на данните към бекенда чрез auth store метода
            await register({
                username: formData.username,
                email: formData.email,
                password: formData.password,
                role: 'viewer' // Задаваме роля "viewer" по подразбиране за нови регистрации
            });
            
            // Успех
            setSuccessMsg('Registration successful! Please sign in.');
            // Пренасочване към страницата за вход след 2 секунди, за да се види съобщението
            setTimeout(() => navigate('/login'), 2000);
        } catch (err: any) {
            // Извличане на съобщението за грешка от FastAPI отговора, ако съществува
            const errorMsg = err.response?.data?.detail || 'Registration failed';
            setError(errorMsg);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-100 to-sky-100 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden border border-blue-100">
                <div className="p-8">
                    {/* Заглавна част */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-50 mb-4 border border-blue-100">
                            <Waves className="w-8 h-8 text-blue-600" />
                        </div>
                        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Create Account</h2>
                        <p className="text-slate-500 mt-2">Join the monitoring network</p>
                    </div>

                    {/* Съобщения за обратна връзка */}
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm text-center">
                            {error}
                        </div>
                    )}
                    {successMsg && (
                        <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-600 rounded-lg text-sm text-center">
                            {successMsg}
                        </div>
                    )}

                    {/* Регистрационен формуляр */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Поле: Потребителско име */}
                        <div className="space-y-1">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                </div>
                                <input
                                    type="text"
                                    name="username"
                                    required
                                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-900 placeholder:text-slate-400"
                                    placeholder="Username"
                                    value={formData.username}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        {/* Поле: Имейл */}
                        <div className="space-y-1">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Mail className="h-5 w-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                </div>
                                <input
                                    type="email"
                                    name="email"
                                    required
                                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-900 placeholder:text-slate-400"
                                    placeholder="Email address"
                                    value={formData.email}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        {/* Поле: Парола */}
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
                                    placeholder="Password"
                                    value={formData.password}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        {/* Поле: Потвърждение на паролата */}
                        <div className="space-y-1">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                </div>
                                <input
                                    type="password"
                                    name="confirmPassword"
                                    required
                                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-900 placeholder:text-slate-400"
                                    placeholder="Confirm password"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all active:scale-[0.98] mt-6"
                        >
                            Register
                        </button>
                    </form>

                    {/* Линк към страницата за вход */}
                    <div className="mt-8 text-center border-t border-slate-100 pt-6">
                        <p className="text-sm text-slate-500">
                            Already have an account?{' '}
                            <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-700 transition-colors">
                                Sign in here
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
