"use client";

import { Fragment, ReactNode } from "react";

interface Props {
  guide: string;
  loading: boolean;
}

type GuideBlock =
  | { type: "heading"; depth: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "unordered-list"; items: string[] }
  | { type: "ordered-list"; items: string[] };

function renderInlineMarkdown(text: string): ReactNode[] {
  return text.split(/(\*\*.*?\*\*)/g).filter(Boolean).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }

    return <Fragment key={index}>{part}</Fragment>;
  });
}

function parseGuide(guide: string): GuideBlock[] {
  const lines = guide.split(/\r?\n/);
  const blocks: GuideBlock[] = [];
  let paragraph: string[] = [];
  let unorderedItems: string[] = [];
  let orderedItems: string[] = [];

  const flushParagraph = () => {
    if (!paragraph.length) {
      return;
    }

    blocks.push({ type: "paragraph", text: paragraph.join(" ").trim() });
    paragraph = [];
  };

  const flushUnorderedList = () => {
    if (!unorderedItems.length) {
      return;
    }

    blocks.push({ type: "unordered-list", items: unorderedItems });
    unorderedItems = [];
  };

  const flushOrderedList = () => {
    if (!orderedItems.length) {
      return;
    }

    blocks.push({ type: "ordered-list", items: orderedItems });
    orderedItems = [];
  };

  const flushAll = () => {
    flushParagraph();
    flushUnorderedList();
    flushOrderedList();
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushAll();
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      flushAll();
      blocks.push({
        type: "heading",
        depth: Math.min(headingMatch[1].length, 6),
        text: headingMatch[2].trim(),
      });
      continue;
    }

    const unorderedMatch = line.match(/^-\s+(.*)$/);
    if (unorderedMatch) {
      flushParagraph();
      flushOrderedList();
      unorderedItems.push(unorderedMatch[1].trim());
      continue;
    }

    const orderedMatch = line.match(/^\d+\.\s+(.*)$/);
    if (orderedMatch) {
      flushParagraph();
      flushUnorderedList();
      orderedItems.push(orderedMatch[1].trim());
      continue;
    }

    flushUnorderedList();
    flushOrderedList();
    paragraph.push(line);
  }

  flushAll();
  return blocks;
}

export default function CVGuide({ guide, loading }: Props) {
  if (!guide && !loading) {
    return (
      <div>
        <h2 className="card-title">Tailored CV Guide</h2>
        <p className="card-subtitle">
          The generated guide will summarize what to emphasize, what gaps to handle carefully, and how
          to rewrite the resume for the chosen job posting.
        </p>
        <div className="guide-box guide-empty">Choose one of the recommended jobs to generate the guide.</div>
      </div>
    );
  }

  if (loading) {
    return <div className="guide-box guide-empty">Generating CV guide...</div>;
  }

  return (
    <div>
      <h2 className="card-title">Tailored CV Guide</h2>
      <p className="card-subtitle">
        This is generated from the selected job description plus the structured profile extracted from
        the LinkedIn paste.
      </p>
      <div className="guide-box guide-markdown">
        {parseGuide(guide).map((block, index) => {
          if (block.type === "heading") {
            if (block.depth <= 3) {
              return <h3 key={index}>{renderInlineMarkdown(block.text)}</h3>;
            }

            if (block.depth === 4) {
              return <h4 key={index}>{renderInlineMarkdown(block.text)}</h4>;
            }

            return <h5 key={index}>{renderInlineMarkdown(block.text)}</h5>;
          }

          if (block.type === "unordered-list") {
            return (
              <ul key={index}>
                {block.items.map((item, itemIndex) => (
                  <li key={itemIndex}>{renderInlineMarkdown(item)}</li>
                ))}
              </ul>
            );
          }

          if (block.type === "ordered-list") {
            return (
              <ol key={index}>
                {block.items.map((item, itemIndex) => (
                  <li key={itemIndex}>{renderInlineMarkdown(item)}</li>
                ))}
              </ol>
            );
          }

          return <p key={index}>{renderInlineMarkdown(block.text)}</p>;
        })}
      </div>
    </div>
  );
}
