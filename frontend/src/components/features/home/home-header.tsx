import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { BrandButton } from "../settings/brand-button";

export function HomeHeader() {
  const { mutate: createConversation } = useCreateConversation();

  return (
    <header className="flex justify-between items-end">
      <section className="flex flex-col gap-5">
        <div
          aria-label="all hands ai logo"
          className="w-[100px] h-[70px] bg-gray-50"
        />
        <h1 className="heading">Let&apos;s Start Building!</h1>
        <p className="text-sm max-w-[424px]">
          OpenHands makes it easy to build and maintain software using AI-driven
          development.
        </p>
      </section>

      <section className="flex flex-col gap-4">
        <BrandButton
          variant="primary"
          type="button"
          className="w-full"
          onClick={() => createConversation({})}
        >
          Launch from Scratch
        </BrandButton>
        <p className="text-sm">
          Not sure how to start?{" "}
          <a
            href="http://"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2"
          >
            Read this
          </a>
        </p>
      </section>
    </header>
  );
}
