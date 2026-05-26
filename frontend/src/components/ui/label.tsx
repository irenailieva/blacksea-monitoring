"use client"

import * as React from "react"
import * as LabelPrimitive from "@radix-ui/react-label"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

// Дефиниране на стиловите варианти за компонента Label (Етикет)
// Използва се за текстови етикети, свързани с полета за въвеждане.
const labelVariants = cva(
    // Базови стилове: малък шрифт, средна плътност, без междуредие.
    // Класовете peer-disabled променят стила, ако свързаният input (със съседен peer клас) е деактивиран.
    "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
)

// Компонент Label
// Обвива Radix UI Label примитива, който осигурява достъпност (напр. автоматично свързване чрез htmlFor).
const Label = React.forwardRef<
    React.ElementRef<typeof LabelPrimitive.Root>,
    React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root> &
    VariantProps<typeof labelVariants>
>(({ className, ...props }, ref) => (
    <LabelPrimitive.Root
        ref={ref}
        className={cn(labelVariants(), className)} // Обединява базовите стилове с подадените чрез className
        {...props}
    />
))
Label.displayName = LabelPrimitive.Root.displayName

export { Label }
