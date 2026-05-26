import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

// Дефиниране на стиловите варианти за компонента Button
// cva (class-variance-authority) управлява комбинациите от класове за цвят (variant) и размер (size).
const buttonVariants = cva(
  // Базови CSS класове, приложени към всеки бутон (напр. центриране, фокус, състояния при деактивация)
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      // Варианти за визуален стил
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      // Варианти за размер
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    // Стойности по подразбиране
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

// Интерфейс за свойствата на бутона.
// Разширява стандартните HTML атрибути за бутон и добавя възможностите за `variant`, `size` и `asChild`.
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  asChild?: boolean; // Ако е true, бутонът ще рендира своя child елемент (напр. <Link>), вместо <div>/<button>
}

// Функционален компонент Button
// Използва forwardRef, за да предава референцията към подлежащия DOM елемент.
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    // Ако asChild е true, използваме Radix UI Slot, който слива проповете със следващия елемент.
    // В противен случай рендираме стандартен HTML <button>.
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props} />
    );
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
