import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { ArrowUp, Bot, ExternalLink, Flag, RotateCcw, Sparkles, UserRound } from "lucide-react";
import { postAnalystQuery } from "../services/api";
import type { AnalystResponse, AnalystRoute, AnalystSource } from "../services/api";
import "./Analyst.css";

type ChatRole = "user" | "assistant";

interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  response?: AnalystResponse;
  failedQuestion?: string;
}

const SUGGESTED_PROMPTS = [
  "Who had the most race wins in 2023?",
  "How did Sainz defend his lead at Singapore?",
  "Why did Verstappen struggle at the 2023 Singapore Grand Prix?",
];

function normalizeSourceUrl(value: string): string | null {
  const trimmed = value.trim();
  const markdownLink = trimmed.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/i);
  const candidate = markdownLink?.[2] ?? trimmed.replace(/^<|>$/g, "");

  try {
    const url = new URL(candidate);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}

function routeLabel(route: AnalystRoute): string {
  return route === "stats" ? "STATS" : route === "narrative" ? "NARRATIVE" : "HYBRID";
}

function getErrorMessage(error: unknown): string {
  const candidate = error as {
    response?: { status?: number; data?: { detail?: unknown } };
    message?: string;
    code?: string;
  };

  const detail = candidate?.response?.data?.detail;
  if (typeof detail === "string" && detail.length > 0) return detail;
  if (candidate?.response?.status === 503) {
    return "The analyst service is temporarily unavailable. Check that the backend and local Ollama models are running, then retry.";
  }
  if (candidate?.code === "ERR_NETWORK") {
    return "Couldn't reach the API. Make sure the FastAPI backend is running at http://localhost:8000 and try again.";
  }
  return candidate?.message || "Something went wrong while answering your question. Please try again.";
}

function SourceList({ sources }: { sources: AnalystSource[] }) {
  if (sources.length === 0) return null;

  return (
    <section className="analyst-sources" aria-label="Answer sources">
      <div className="analyst-sources-heading">SOURCES <span>{sources.length}</span></div>
      <div className="analyst-source-list">
        {sources.map((source, index) => {
          const href = normalizeSourceUrl(source.source_url);
          return (
            <article className="analyst-source" key={`${source.title}-${source.source_url}-${index}`}>
              <div className="analyst-source-icon"><Flag size={14} /></div>
              <div className="analyst-source-details">
                <strong>{source.title}</strong>
                <span>{[source.event_name, source.season].filter(Boolean).join(" · ") || "Race report"}</span>
                {href ? (
                  <a href={href} target="_blank" rel="noreferrer">
                    Open source <ExternalLink size={12} aria-hidden="true" />
                  </a>
                ) : (
                  <span className="analyst-source-unavailable">Source link unavailable</span>
                )}
              </div>
              {typeof source.distance === "number" && (
                <span className="analyst-source-distance" title="Vector distance">
                  {source.distance.toFixed(3)}
                </span>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default function Analyst() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryQuestion, setRetryQuestion] = useState<string | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const idCounter = useRef(0);

  const createId = () => {
    idCounter.current += 1;
    return `analyst-${Date.now()}-${idCounter.current}`;
  };

  useEffect(() => {
    const transcript = transcriptRef.current;
    if (transcript) transcript.scrollTop = transcript.scrollHeight;
  }, [messages, isLoading]);

  const submitQuestion = async (rawQuestion: string) => {
    const cleanQuestion = rawQuestion.trim();
    if (cleanQuestion.length < 3 || isLoading) {
      if (cleanQuestion.length > 0 && cleanQuestion.length < 3) {
        setError("Enter at least 3 characters to ask a question.");
      }
      return;
    }

    setError(null);
    setRetryQuestion(null);
    setQuestion("");
    setIsLoading(true);
    setMessages((current) => [
      ...current,
      { id: createId(), role: "user", text: cleanQuestion },
    ]);

    try {
      const response = await postAnalystQuery(cleanQuestion);
      setMessages((current) => [
        ...current,
        { id: createId(), role: "assistant", text: response.answer, response },
      ]);
    } catch (requestError) {
      const message = getErrorMessage(requestError);
      setError(message);
      setRetryQuestion(cleanQuestion);
      setMessages((current) => [
        ...current,
        {
          id: createId(),
          role: "assistant",
          text: message,
          failedQuestion: cleanQuestion,
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void submitQuestion(question);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitQuestion(question);
    }
  };

  const choosePrompt = (prompt: string) => {
    setQuestion(prompt);
    setError(null);
    inputRef.current?.focus();
  };

  const retryLastQuestion = () => {
    if (retryQuestion) void submitQuestion(retryQuestion);
  };

  return (
    <div className="analyst-page">
      <header className="analyst-page-heading">
        <div>
          <span className="eyebrow">RACE INTELLIGENCE / AI</span>
          <h2>AI Race Analyst</h2>
          <p>Ask about race results, strategy decisions, and the story behind the numbers.</p>
        </div>
        <div className="analyst-engine-status"><span /> HYBRID RAG ENGINE</div>
      </header>

      <section className="analyst-workspace" aria-label="AI Race Analyst chat">
        <div className="analyst-chat-topline">
          <div className="analyst-chat-title">
            <div className="analyst-chat-avatar"><Bot size={19} /></div>
            <div><strong>RaceLab Analyst</strong><span>Statistics + race report retrieval</span></div>
          </div>
          <div className="analyst-chat-note"><Sparkles size={13} /> Evidence-led answers</div>
        </div>

        <div className={`analyst-transcript${messages.length === 0 ? " is-empty" : ""}`} ref={transcriptRef} role="log" aria-live="polite" aria-relevant="additions text">
          {messages.length === 0 ? (
            <div className="analyst-empty-state">
              <div className="analyst-empty-orb"><Bot size={26} /></div>
              <span className="eyebrow">YOUR RACE INTELLIGENCE DESK</span>
              <h3>What do you want to know?</h3>
              <p>Ask a direct stats question or explore the context behind a race strategy. Answers include available source links.</p>
              <div className="analyst-prompt-grid">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button className="analyst-prompt" key={prompt} onClick={() => choosePrompt(prompt)} type="button">
                    <span>{prompt}</span><ArrowUp size={15} />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="analyst-messages">
              {messages.map((message) => (
                <article className={`analyst-message analyst-message--${message.role}`} key={message.id}>
                  <div className="analyst-message-avatar" aria-hidden="true">
                    {message.role === "user" ? <UserRound size={16} /> : <Bot size={16} />}
                  </div>
                  <div className="analyst-message-content">
                    <div className="analyst-message-meta">
                      <strong>{message.role === "user" ? "You" : "RaceLab Analyst"}</strong>
                      {message.response && <span className={`analyst-route-chip analyst-route-chip--${message.response.route}`}>{routeLabel(message.response.route)}</span>}
                      {message.failedQuestion && <span className="analyst-route-chip analyst-route-chip--error">REQUEST FAILED</span>}
                    </div>
                    <p className="analyst-message-text">{message.text}</p>
                    {message.response && <SourceList sources={message.response.sources} />}
                    {message.failedQuestion && retryQuestion === message.failedQuestion && !isLoading && (
                      <button className="analyst-retry-button" type="button" onClick={retryLastQuestion}>
                        <RotateCcw size={13} /> Retry question
                      </button>
                    )}
                  </div>
                </article>
              ))}
              {isLoading && (
                <div className="analyst-loading-row" role="status" aria-label="Generating answer">
                  <div className="analyst-message-avatar"><Bot size={16} /></div>
                  <div className="analyst-loading-bubble"><span /><span /><span /><em>Checking race data and sources…</em></div>
                </div>
              )}
            </div>
          )}
        </div>

        <form className="analyst-composer" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="analyst-question">Ask the AI Race Analyst</label>
          <textarea
            id="analyst-question"
            ref={inputRef}
            value={question}
            onChange={(event) => {
              setQuestion(event.target.value);
              if (error) setError(null);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about a driver, race, or strategy decision…"
            rows={2}
            maxLength={1000}
            disabled={isLoading}
            aria-describedby="analyst-composer-hint"
          />
          <div className="analyst-composer-bottom">
            <span id="analyst-composer-hint">Enter to send · Shift + Enter for a new line · 1000 character limit</span>
            <button className="analyst-send-button" type="submit" disabled={isLoading || question.trim().length < 3} aria-label="Send question">
              {isLoading ? <span className="analyst-send-spinner" /> : <ArrowUp size={18} />}
              <span>{isLoading ? "Thinking" : "Ask Analyst"}</span>
            </button>
          </div>
          {error && <p className="analyst-inline-error" role="alert">{error}</p>}
        </form>
      </section>
      <p className="analyst-disclaimer">Answers are based on available race data and retrieved reports. Verify source material for critical decisions.</p>
    </div>
  );
}
