import React from "react";
import { useTranslation } from "react-i18next";
import { BrandButton } from "#/components/features/settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useSettings } from "#/hooks/query/use-settings";

export default function ChatRoute() {
  const { t } = useTranslation();
  const { data: settings, isFetching } = useSettings();

  const [prompt, setPrompt] = React.useState("");
  const [messages, setMessages] = React.useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [isSending, setIsSending] = React.useState(false);

  const sendMessage = async () => {
    if (!prompt.trim()) return;
    const userMsg = { role: "user" as const, content: prompt };
    setMessages((m) => [...m, userMsg]);
    setPrompt("");
    setIsSending(true);
    try {
      // TODO: integrate with backend streaming endpoint /api/chat
      // For now, mock assistant reply
      setTimeout(() => {
        setMessages((m) => [...m, { role: "assistant", content: "(demo) Received: " + userMsg.content }]);
        setIsSending(false);
      }, 600);
    } catch {
      setIsSending(false);
    }
  };

  const [imagePrompt, setImagePrompt] = React.useState("");
  const [videoPrompt, setVideoPrompt] = React.useState("");
  const [jobStatus, setJobStatus] = React.useState<string | null>(null);

  const generateImage = async () => {
    if (!imagePrompt.trim()) return;
    setJobStatus("Creating image...");
    // TODO: call POST /api/generate-image, then poll /api/jobs/{id}
    setTimeout(() => setJobStatus("(demo) Image ready"), 1200);
  };

  const generateVideo = async () => {
    if (!videoPrompt.trim()) return;
    setJobStatus("Creating video...");
    // TODO: call POST /api/generate-video, then poll /api/jobs/{id}
    setTimeout(() => setJobStatus("(demo) Video ready"), 2500);
  };

  return (
    <div className="flex flex-col gap-6 p-6 w-full h-full overflow-auto">
      <h1 className="text-2xl font-semibold text-white">General AI Chat</h1>

      {isFetching ? (
        <div className="flex items-center gap-2 text-[#9099AC]">
          <LoadingSpinner size="small" /> {t("LOADING$SETTINGS")}
        </div>
      ) : (
        <div className="text-[#9099AC] text-sm">
          Model: <span className="text-white">{settings?.LLM?.MODEL || settings?.llm_model || "(not set)"}</span>
        </div>
      )}

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="col-span-2 card-glow-accent p-4 h-[60vh] flex flex-col">
          <div className="flex-1 overflow-auto flex flex-col gap-3 pr-1">
            {messages.map((m, idx) => (
              <div key={idx} className={m.role === "user" ? "text-white" : "text-glow"}>
                <span className="text-xs opacity-70 mr-2">{m.role}</span>
                {m.content}
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 mt-3">
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder={"Ask anything..."}
              className="flex-1 bg-tertiary border border-[#717888] rounded-sm p-2 text-white"
            />
            <BrandButton
              variant="primary"
              type="button"
              onClick={sendMessage}
              isDisabled={isSending || !prompt.trim()}
              className="btn-3d"
            >
              {isSending ? t("SENDING") : t("SEND")}
            </BrandButton>
          </div>
        </div>

        <div className="col-span-1 flex flex-col gap-4">
          <div className="card-glow-gold p-4">
            <h2 className="text-white font-medium mb-2">Generate Image</h2>
            <input
              value={imagePrompt}
              onChange={(e) => setImagePrompt(e.target.value)}
              placeholder={"Describe your image..."}
              className="w-full bg-tertiary border border-[#717888] rounded-sm p-2 text-white mb-2"
            />
            <BrandButton
              variant="glow"
              type="button"
              onClick={generateImage}
              isDisabled={!imagePrompt.trim()}
              className="btn-3d"
            >
              {t("GENERATE_IMAGE")}
            </BrandButton>
          </div>

          <div className="card-glow-gold p-4">
            <h2 className="text-white font-medium mb-2">Generate Video</h2>
            <input
              value={videoPrompt}
              onChange={(e) => setVideoPrompt(e.target.value)}
              placeholder={"Describe your video..."}
              className="w-full bg-tertiary border border-[#717888] rounded-sm p-2 text-white mb-2"
            />
            <BrandButton
              variant="glow"
              type="button"
              onClick={generateVideo}
              isDisabled={!videoPrompt.trim()}
              className="btn-3d"
            >
              {t("GENERATE_VIDEO")}
            </BrandButton>
          </div>

          {jobStatus && (
            <div className="text-[#9099AC] text-sm">{jobStatus}</div>
          )}
        </div>
      </section>
    </div>
  );
}