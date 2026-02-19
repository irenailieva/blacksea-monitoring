import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import useAuth from "@/store/useAuth"

export default function Settings() {
    const { user } = useAuth()

    return (
        <div className="flex min-h-screen w-full flex-col">
            <main className="flex min-h-[calc(100vh_-_theme(spacing.16))] flex-1 flex-col gap-4 bg-muted/40 p-4 md:gap-8 md:p-10">
                <div className="mx-auto grid w-full max-w-6xl gap-2">
                    <h1 className="text-3xl font-semibold">Settings</h1>
                </div>
                <div className="mx-auto grid w-full max-w-6xl items-start gap-6 md:grid-cols-[180px_1fr] lg:grid-cols-[250px_1fr]">
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
                        <Card>
                            <CardHeader>
                                <CardTitle>Display Name</CardTitle>
                                <CardDescription>
                                    This is your public display name. It can be your real name or a pseudonym.
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form>
                                    <Input placeholder="Store Name" defaultValue={user?.email?.split('@')[0] || "User"} />
                                </form>
                            </CardContent>
                            <CardFooter className="border-t px-6 py-4">
                                <Button>Save</Button>
                            </CardFooter>
                        </Card>
                        <Card>
                            <CardHeader>
                                <CardTitle>Notifications</CardTitle>
                                <CardDescription>
                                    Configure how you receive notifications.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="grid gap-4">
                                <div className="-mx-2 flex items-start space-x-4 rounded-md p-2 transition-all hover:bg-accent hover:text-accent-foreground">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium leading-none">Everything</p>
                                        <p className="text-sm text-muted-foreground">
                                            Email digest, mentions & all activity.
                                        </p>
                                    </div>
                                    <div className="ml-auto">
                                        <input type="checkbox" id="notify-everything" className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" />
                                    </div>
                                </div>
                                <div className="-mx-2 flex items-start space-x-4 rounded-md bg-accent p-2 text-accent-foreground transition-all">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium leading-none">Available</p>
                                        <p className="text-sm text-muted-foreground">
                                            Only mentions and comments.
                                        </p>
                                    </div>
                                    <div className="ml-auto">
                                        <input type="checkbox" id="notify-available" defaultChecked className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" />
                                    </div>
                                </div>
                                <div className="-mx-2 flex items-start space-x-4 rounded-md p-2 transition-all hover:bg-accent hover:text-accent-foreground">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium leading-none">Ignoring</p>
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
            </main>
        </div>
    )
}
