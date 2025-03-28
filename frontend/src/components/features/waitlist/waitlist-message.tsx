interface WaitlistMessageProps {
  content: "waitlist" | "sign-in";
}

export function WaitlistMessage({ content }: WaitlistMessageProps) {
  return (
    <div className="flex flex-col gap-2 w-full items-center text-center">
      <h1 className="text-2xl font-bold">
        {content === "sign-in" && "Sign in with GitHub"}
        {content === "waitlist" && "Just a little longer!"}
      </h1>
      {/* Sign-in message without waitlist reference */}
      {content === "waitlist" && (
        <p className="text-sm">
          Thanks for your patience! We&apos;re accepting new members
          progressively. If you haven&apos;t joined the waitlist yet, now&apos;s
          the time!
        </p>
      )}
    </div>
  );
}
