import React from "react";

interface CarouselSlide {
  image: string;
  title: string;
  description: string;
  buttonText?: string;
  buttonHref?: string;
}

const slides: CarouselSlide[] = [
  {
    image: "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=400&h=200&fit=crop&crop=center",
    title: "All Hands Hackathon 2026",
    description: "Join our global hackathon and build the future of AI-powered development. Prizes, workshops, and more!",
    buttonText: "Register",
    buttonHref: "https://all-hands.dev/hackathon",
  },
  {
    image: "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=400&h=200&fit=crop&crop=center",
    title: "How OpenHands Works",
    description: "Read our latest article on how OpenHands is democratizing AI for all developers.",
    buttonText: "Read Article",
    buttonHref: "https://blog.all-hands.dev/openhands-works",
  },
  {
    image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=200&fit=crop&crop=center",
    title: "Community Slack",
    description: "Join our Slack to connect with thousands of developers, get help, and share your projects.",
    buttonText: "Join Slack",
    buttonHref: "https://join.slack.com/t/openhands-ai/shared_invite/zt-34zm4j0gj-Qz5kRHoca8DFCbqXPS~f_A",
  },
];

export function EventCarousel() {
  const [current, setCurrent] = React.useState(0);
  const goTo = (idx: number) => setCurrent(idx);
  // const prev = () => setCurrent((c) => (c === 0 ? slides.length - 1 : c - 1));
  // const next = () => setCurrent((c) => (c === slides.length - 1 ? 0 : c + 1));

  return (
    <div
      className="w-full mx-auto bg-[#3887f6] rounded-2xl p-6 flex flex-col items-center shadow-lg relative"
      style={{ height: "508px" }}
    >
      <div className="flex flex-col items-center flex-1 justify-center max-w-sm">
        <img
          src={slides[current].image}
          alt={slides[current].title}
          className="w-full h-32 object-cover rounded-xl mb-6"
        />
        <h3 className="text-2xl font-black text-white mb-3 leading-tight text-center">
          {slides[current].title}
        </h3>
        <p className="text-sm text-black/80 mb-6 text-center leading-relaxed">
          {slides[current].description}
        </p>
        {slides[current].buttonText && slides[current].buttonHref && (
          <a
            href={slides[current].buttonHref}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 rounded-lg bg-black text-white font-semibold text-base shadow hover:bg-neutral-800 transition-colors"
          >
            {slides[current].buttonText}
          </a>
        )}
      </div>
      {/* Carousel dots sticky to bottom */}
      <div className="flex gap-2 mt-auto pt-4">
        {slides.map((_, idx) => (
          <button
            key={idx}
            className={`w-3 h-3 rounded-full transition-colors ${
              idx === current
                ? "bg-white"
                : "bg-white/20 hover:bg-white/40"
            }`}
            onClick={() => goTo(idx)}
            aria-label={`Go to slide ${idx + 1}`}
          />
        ))}
      </div>
      {/* Carousel arrows (commented out) */}
      {/*
      <button
        className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/30 hover:bg-black/60 text-white rounded-full w-8 h-8 flex items-center justify-center"
        onClick={prev}
        aria-label="Previous slide"
      >
        <span className="text-lg">&#8592;</span>
      </button>
      <button
        className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/30 hover:bg-black/60 text-white rounded-full w-8 h-8 flex items-center justify-center"
        onClick={next}
        aria-label="Next slide"
      >
        <span className="text-lg">&#8594;</span>
      </button>
      */}
    </div>
  );
}
