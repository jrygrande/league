"use client"

import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { useUser } from "@/hooks/useUser"
import { User } from "@/lib/types"

const usernameSchema = z.object({
  username: z
    .string()
    .min(1, "Username is required")
    .min(3, "Username must be at least 3 characters")
    .max(20, "Username must be less than 20 characters")
    .regex(/^[a-zA-Z0-9_-]+$/, "Username can only contain letters, numbers, underscores, and hyphens")
})

type UsernameFormData = z.infer<typeof usernameSchema>

interface UsernameFormProps {
  onUserFound: (user: User) => void
  initialUsername?: string
}

export function UsernameForm({ onUserFound, initialUsername = "" }: UsernameFormProps) {
  const [submittedUsername, setSubmittedUsername] = useState(initialUsername)
  
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    getValues,
  } = useForm<UsernameFormData>({
    resolver: zodResolver(usernameSchema),
    defaultValues: { username: initialUsername },
    mode: "onChange",
  })

  const {
    data: user,
    isLoading,
    error,
  } = useUser(submittedUsername)

  // Handle successful user fetch
  useEffect(() => {
    if (user && submittedUsername) {
      onUserFound(user)
    }
  }, [user, submittedUsername, onUserFound])

  const onSubmit = (data: UsernameFormData) => {
    setSubmittedUsername(data.username)
  }

  return (
    <div className="w-full max-w-md space-y-4">
      <div className="space-y-2">
        <label htmlFor="username" className="text-sm font-medium leading-none">
          Sleeper Username
        </label>
        <form onSubmit={handleSubmit(onSubmit)} className="flex gap-2">
          <Input
            id="username"
            placeholder="Enter your Sleeper username"
            {...register("username")}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!isValid || isLoading}
            className="shrink-0"
          >
            {isLoading ? "Finding..." : "Find User"}
          </Button>
        </form>
        
        {errors.username && (
          <p className="text-sm text-red-600">
            {errors.username.message}
          </p>
        )}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      )}

      {/* Error state */}
      {error && submittedUsername && (
        <Alert variant="destructive">
          <AlertDescription>
            {error.response?.status === 404
              ? `User "${submittedUsername}" not found. Please check the username and try again.`
              : "Failed to fetch user data. Please try again."
            }
          </AlertDescription>
        </Alert>
      )}

      {/* Success state */}
      {user && submittedUsername && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-3">
            {user.avatar && (
              <img
                src={`https://sleepercdn.com/avatars/thumbs/${user.avatar}`}
                alt={`${user.display_name || user.username}'s avatar`}
                className="w-10 h-10 rounded-full"
              />
            )}
            <div>
              <p className="font-medium text-green-900">
                {user.display_name || user.username}
              </p>
              <p className="text-sm text-green-700">@{user.username}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}