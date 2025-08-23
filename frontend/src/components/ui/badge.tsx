import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "../../lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-[#D9653B] text-white hover:bg-[#C55A32]",
        secondary:
          "border-transparent bg-[#A1A1A1]/20 text-white hover:bg-[#A1A1A1]/30",
        destructive:
          "border-transparent bg-[#B94A3D] text-white hover:bg-[#A13F33]",
        outline: "border-[#A1A1A1]/30 text-[#A1A1A1]",
        success:
          "border-transparent bg-[#B97A3D] text-white hover:bg-[#A36A34]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
