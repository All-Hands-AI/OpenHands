import { useEffect, useState } from "react"

const DynamicText = ({ items }) => {
  const [index, setIndex] = useState(0)
  const [fade, setFade] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      // Fade out
      setFade(false)
      setTimeout(() => {
        // Change text and fade back in
        setIndex((prev) => (prev + 1) % items.length)
        setFade(true)
      }, 500) // duration of fade out
    }, 5000)

    return () => clearInterval(interval)
  }, [items.length])

  return (
    <div
      key={index}
      className={`transform text-sm font-medium italic text-neutral-100 transition-all duration-500 ease-in-out ${fade ? "translate-y-0 opacity-100" : "-translate-y-2 opacity-0"}`}
    >
      {items[index]}
    </div>
  )
}

export default DynamicText
