import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import useAuth from "@/store/useAuth"

// Страница "Настройки" (Settings)
// Предоставя потребителски интерфейс за конфигуриране на профила и предпочитанията за известия.
export default function Settings() {
    // Вземане на текущия потребител от глобалното състояние (Zustand)
    const { user } = useAuth()

    return (
        <div className="h-full overflow-y-auto pr-2">
            {/* Заглавна част */}
            <div className="mx-auto grid w-full max-w-6xl gap-2 py-6">
                <h1 className="text-3xl font-semibold">Settings</h1>
            </div>
            
            {/* Основен изглед с навигация вляво и съдържание вдясно */}
            <div className="mx-auto grid w-full max-w-6xl items-start gap-6 md:grid-cols-[180px_1fr] lg:grid-cols-[250px_1fr] pb-10">
                {/* Странична навигация (За момента статична, но подготвена за бъдещо разширение) */}
                <nav className="grid gap-4 text-sm text-muted-foreground">
                    <a href="#" className="font-semibold text-primary">
                        General
                    </a>
                    <a href="#">Security</a>
                    <a href="#">Integrations</a>
                    <a href="#">Support</a>
                    <a href="#">Organizations</a>
                    <a href="#">Advanced</a>
                </nav>
                
                <div className="grid gap-6">
                    {/* Карта за настройки на потребителския профил */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Username</CardTitle>
                            <CardDescription>
                                This is your public display name. It can be your real name or a pseudonym.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form>
                                {/* Полето е предварително попълнено с името на логнатия потребител */}
                                <Input placeholder="Name" defaultValue={user?.username || ""} />
                            </form>
                        </CardContent>
                        <CardFooter className="border-t px-6 py-4">
                            <Button>Save</Button>
                        </CardFooter>
                    </Card>

                    {/* Карта за настройки на известията */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Notifications</CardTitle>
                            <CardDescription>
                                Configure how you receive system notifications.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="grid gap-4">
                            {/* Опция: Всички известия */}
                            <div className="-mx-2 flex items-start space-x-4 rounded-md p-2 transition-all hover:bg-accent hover:text-accent-foreground">
                                <div className="space-y-1">
                                    <p className="text-sm font-medium leading-none">Everything</p>
                                    <p className="text-sm text-muted-foreground">
                                        Email digests, mentions, and all activity (e.g., completed ETL).
                                    </p>
                                </div>
                                <div className="ml-auto">
                                    <input type="checkbox" id="notify-everything" className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" />
                                </div>
                            </div>
                            
                            {/* Опция: Само важни (избрана по подразбиране) */}
                            <div className="-mx-2 flex items-start space-x-4 rounded-md bg-accent p-2 text-accent-foreground transition-all">
                                <div className="space-y-1">
                                    <p className="text-sm font-medium leading-none">Important only</p>
                                    <p className="text-sm text-muted-foreground">
                                        Only critical errors and system warnings.
                                    </p>
                                </div>
                                <div className="ml-auto">
                                    <input type="checkbox" id="notify-available" defaultChecked className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" />
                                </div>
                            </div>
                            
                            {/* Опция: Без известия */}
                            <div className="-mx-2 flex items-start space-x-4 rounded-md p-2 transition-all hover:bg-accent hover:text-accent-foreground">
                                <div className="space-y-1">
                                    <p className="text-sm font-medium leading-none">Ignore</p>
                                    <p className="text-sm text-muted-foreground">
                                        Turn off all notifications.
                                    </p>
                                </div>
                                <div className="ml-auto">
                                    <input type="checkbox" id="notify-ignoring" className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" />
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="border-t px-6 py-4">
                            <Button>Save</Button>
                        </CardFooter>
                    </Card>
                </div>
            </div>
        </div>
    )
}
