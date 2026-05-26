import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

// Дефиниране на стиловите варианти за компонента Badge (Етикет/Значка)
// Използва се class-variance-authority (cva) за лесно управление на CSS класовете
// въз основа на подадените пропъртита (варианти).
const badgeVariants = cva(
    // Базови класове, приложими за всички варианти
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
        variants: {
            // Различни цветови теми (variants)
            variant: {
                default:
                    "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
                secondary:
                    "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
                destructive:
                    "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
                outline: "text-foreground",
            },
        },
        defaultVariants: {
            variant: "default", // По подразбиране се използва "default" темата
        },
    }
)

// Интерфейс, описващ свойствата (props) на Badge компонента.
// Наследява стандартните HTML атрибути за div и вариантите от cva.
export interface BadgeProps
    extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> { }

// Функционален компонент Badge
// Визуализира малък етикет (значка), често използван за статуси или категоризации.
function Badge({ className, variant, ...props }: BadgeProps) {
    return (
        <div className={cn(badgeVariants({ variant }), className)} {...props} />
    )
}

export { Badge, badgeVariants }
