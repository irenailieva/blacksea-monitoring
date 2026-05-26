import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"

import { cn } from "@/lib/utils"

// Компонент Progress (Лента за напредък)
// Използва Radix UI Progress примитива за семантично коректна и достъпна индикация на процес (напр. качване, ETL прогрес).
const Progress = React.forwardRef<
    React.ElementRef<typeof ProgressPrimitive.Root>,
    React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
    // Коренният елемент действа като фон (track) на лентата за напредък.
    <ProgressPrimitive.Root
        ref={ref}
        className={cn(
            "relative h-4 w-full overflow-hidden rounded-full bg-secondary",
            className
        )}
        {...props}
    >
        {/* Индикаторът представлява запълнената част от лентата.
            Изместването по оста X (translateX) се използва за визуално контролиране на напредъка.
            Ако value е 0 или undefined, индикаторът се скрива (измества се със -100%).
            Ако value е 100, изместването е 0% (напълно запълнена). */}
        <ProgressPrimitive.Indicator
            className="h-full w-full flex-1 bg-primary transition-all"
            style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
        />
    </ProgressPrimitive.Root>
))
Progress.displayName = ProgressPrimitive.Root.displayName

export { Progress }
