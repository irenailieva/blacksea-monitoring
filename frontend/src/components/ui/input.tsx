import * as React from "react"

import { cn } from "@/lib/utils"

// Компонент Input (Текстово поле)
// Използва се за въвеждане на данни от потребителя. Стилизиран е съобразно общата тема.
const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        // cn() обединява стандартните стилове (бордюр, фон, фокус ринг) с допълнителни класове (className)
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className
        )}
        ref={ref} // Позволява достъп до DOM елемента от родителски компоненти
        {...props} // Предава всички останали атрибути (напр. onChange, value, placeholder)
      />
    );
  }
)
Input.displayName = "Input"

export { Input }
