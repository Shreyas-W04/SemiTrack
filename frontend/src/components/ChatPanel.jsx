import { useEffect, useMemo, useRef } from "react";

const MAX_VISIBLE_FACTS = 2;
const MAX_VISIBLE_CITATIONS = 2;

function renderInline(text) {
  const safe = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return safe.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`strong-${index}`}>{part.slice(2, -2)}</strong>;
    }
    return <span key={`text-${index}`}>{part}</span>;
  });
}

function clipSentences(text, maxSentences) {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "";
  }

  const protectedText = normalized.replace(/(\d)\.(\d)/g, "$1__DECIMAL__$2");
  const sentences = protectedText.match(/[^.!?]+[.!?]?/g)?.map((part) => part.trim()).filter(Boolean) || [protectedText];
  return sentences
    .slice(0, maxSentences)
    .join(" ")
    .replace(/__DECIMAL__/g, ".")
    .trim();
}

function truncateText(text, maxLength = 180) {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (normalized.length <= maxLength) {
    return normalized;
  }
  return `${normalized.slice(0, maxLength - 3).trimEnd()}...`;
}

function normalizeAssistantContent(content) {
  const lines = content
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const prose = [];
  const bullets = [];

  lines.forEach((rawLine) => {
    const line = rawLine.replace(/^#{1,6}\s+/, "").trim();
    if (!line) {
      return;
    }

    const bulletMatch = line.match(/^[-*]\s+(.*)$/) || line.match(/^\d+[.)]\s+(.*)$/);
    if (bulletMatch) {
      bullets.push(bulletMatch[1].trim());
      return;
    }

    prose.push(line);
  });

  const normalizedBullets = bullets.map((item) => clipSentences(item, 1)).filter(Boolean);
  let lead = prose.join(" ").replace(/\s+/g, " ").trim();

  if (!lead && normalizedBullets.length) {
    lead = normalizedBullets.shift();
  }

  lead = clipSentences(lead, normalizedBullets.length ? 2 : 3);

  const blocks = [];
  if (lead) {
    blocks.push(lead);
  }
  if (normalizedBullets.length) {
    blocks.push(
      normalizedBullets
        .slice(0, 2)
        .map((item) => `- ${item}`)
        .join("\n")
    );
  }

  return blocks.join("\n\n").trim();
}

function renderMarkdown(content) {
  const blocks = content.trim().split(/\n\s*\n/).filter(Boolean);

  return blocks.map((block, blockIndex) => {
    const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
    if (!lines.length) {
      return null;
    }

    if (lines.every((line) => line.startsWith("- "))) {
      return (
        <ul key={`ul-${blockIndex}`} className="md-list">
          {lines.map((line, index) => (
            <li key={`li-${blockIndex}-${index}`}>{renderInline(line.slice(2))}</li>
          ))}
        </ul>
      );
    }

    if (lines.every((line) => /^\d+\.\s+/.test(line))) {
      return (
        <ol key={`ol-${blockIndex}`} className="md-list md-ordered">
          {lines.map((line, index) => (
            <li key={`oli-${blockIndex}-${index}`}>{renderInline(line.replace(/^\d+\.\s+/, ""))}</li>
          ))}
        </ol>
      );
    }

    const headingMatch = lines[0].match(/^(#{1,4})\s+(.*)$/);
    if (headingMatch) {
      const bodyLines = lines.slice(1);
      return (
        <div key={`heading-${blockIndex}`} className="md-block">
          <p className="md-paragraph md-paragraph-strong">{renderInline(headingMatch[2])}</p>
          {bodyLines.length ? <p className="md-paragraph">{renderInline(bodyLines.join(" "))}</p> : null}
        </div>
      );
    }

    return (
      <p key={`p-${blockIndex}`} className="md-paragraph">
        {renderInline(lines.join(" "))}
      </p>
    );
  });
}

function SupportBlock({ label, count, children, defaultOpen = false }) {
  return (
    <details className="chat-support-block" open={defaultOpen}>
      <summary>
        <span>{label}</span>
        <strong>{count}</strong>
      </summary>
      <div className="chat-support-content">{children}</div>
    </details>
  );
}

function Message({ message }) {
  const content = message.role === "assistant" ? normalizeAssistantContent(message.content) : message.content;
  const facts = message.exactFacts || [];
  const citations = message.citations || [];
  const visibleFacts = facts.slice(0, MAX_VISIBLE_FACTS);
  const visibleCitations = citations.slice(0, MAX_VISIBLE_CITATIONS);
  const hiddenFactCount = Math.max(0, facts.length - visibleFacts.length);
  const hiddenCitationCount = Math.max(0, citations.length - visibleCitations.length);

  return (
    <article className={`chat-message ${message.role === "assistant" ? "assistant" : "user"}`}>
      <div className="chat-message-top">
        <div className="chat-role">{message.role === "assistant" ? "SemiTrack AI" : "You"}</div>
        {message.model ? <div className="chat-model-chip">{message.model}</div> : null}
      </div>

      <div className="chat-body markdown-body">{renderMarkdown(content)}</div>

      {facts.length || citations.length ? (
        <div className="chat-support">
          {visibleFacts.length ? (
            <SupportBlock label="Key facts" count={facts.length}>
              <ul className="support-list">
                {visibleFacts.map((fact) => (
                  <li key={fact}>{fact}</li>
                ))}
              </ul>
              {hiddenFactCount ? <div className="chat-support-note">Showing {visibleFacts.length} of {facts.length} extracted facts.</div> : null}
            </SupportBlock>
          ) : null}

          {visibleCitations.length ? (
            <SupportBlock label="Sources" count={citations.length}>
              <div className="chat-citations">
                {visibleCitations.map((citation) => (
                  <div key={`${citation.label}-${citation.title}`} className="citation-card">
                    <div className="citation-topline">
                      <strong>{citation.label}</strong>
                      <span>{citation.kind}</span>
                    </div>
                    <div className="citation-title">{citation.title}</div>
                    <div className="citation-source">{citation.source}</div>
                    {citation.snippet ? <div className="citation-snippet">{truncateText(citation.snippet, 170)}</div> : null}
                  </div>
                ))}
              </div>
              {hiddenCitationCount ? (
                <div className="chat-support-note">Showing {visibleCitations.length} of {citations.length} source excerpts.</div>
              ) : null}
            </SupportBlock>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

export default function ChatPanel({
  messages,
  draft,
  setDraft,
  onSubmit,
  pending,
  suggestions,
  contextLabel,
  error
}) {
  const logRef = useRef(null);

  const visibleSuggestions = useMemo(() => suggestions.slice(0, 5), [suggestions]);
  const showEmptyState = messages.length === 1 && messages[0]?.role === "assistant";
  const renderedMessages = showEmptyState ? [] : messages;

  useEffect(() => {
    const node = logRef.current;
    if (!node) {
      return;
    }
    node.scrollTop = node.scrollHeight;
  }, [messages, pending]);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit(draft);
  };

  return (
    <aside className="chat-panel">
      <div className="chat-panel-top">
        <div className="chat-panel-head">
          <div>
            <div className="chat-kicker">RAG Workspace</div>
            <h2>Ask the data, not the vibe.</h2>
          </div>
          <div className="chat-context">{contextLabel}</div>
        </div>

        <p className="chat-panel-copy">Local RAG only: report text, chart notes, and processed CSVs. No internet browsing.</p>
        <p className="chat-panel-copy chat-panel-copy-secondary">Ask what changed, why a year moved, or whether a visible drop is actually real.</p>

        <div className="chat-suggestions">
          {visibleSuggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              className="suggestion-pill"
              disabled={pending}
              onClick={() => onSubmit(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      <div ref={logRef} className="chat-log">
        {showEmptyState ? (
          <div className="chat-empty-state">
            <div className="chat-empty-title">Start with a conclusion-seeking question.</div>
            <p>Good prompts ask what changed, why the evidence supports a claim, or how two years differ.</p>
            <ul className="chat-empty-list">
              <li>Ask for a year comparison while compare mode is active.</li>
              <li>Ask why a chart matters if you want a quick interpretation.</li>
              <li>Open the evidence blocks only when you want the supporting facts.</li>
            </ul>
          </div>
        ) : null}

        {renderedMessages.map((message, index) => (
          <Message key={`${message.role}-${index}`} message={message} />
        ))}
      </div>

      <div className="chat-panel-bottom">
        {error ? <div className="chat-error">{error}</div> : null}

        <form className="chat-form" onSubmit={handleSubmit}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask why there is no substitution through 2024, or compare 2018 and 2024..."
            rows={3}
          />
          <div className="chat-form-footer">
            <span className="chat-form-hint">Answers lead with the conclusion and keep the evidence collapsible.</span>
            <button type="submit" className="chat-submit" disabled={pending || !draft.trim()}>
              {pending ? "Thinking..." : "Send to SemiTrack AI"}
            </button>
          </div>
        </form>
      </div>
    </aside>
  );
}
