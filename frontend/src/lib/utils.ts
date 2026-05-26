import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

// Помощна функция за обединяване на Tailwind CSS класове
// Тя взема произволен брой аргументи за класове (включително условни) чрез clsx
// и ги прекарва през twMerge, за да разреши конфликти (напр. 'p-4' и 'p-2' -> остава 'p-2')
// Това е особено полезно при създаването на преизползваеми компоненти (напр. със shadcn/ui).
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}
