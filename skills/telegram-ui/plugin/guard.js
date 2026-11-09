// Repair only the proven rich-Markdown heading boundary. Code and block-level
// HTML islands are protected so an unrelated rich structure does not disable
// inspection of the rest of the message.
const BLOCK_TAGS = [
  "aside", "blockquote", "code", "details", "figure", "ol", "pre", "table",
  "tg-collage", "tg-math-block", "tg-slideshow", "ul",
];

function protectedRanges(text) {
  const ranges = [];

  for (let index = 0; index < text.length;) {
    if (text[index] !== "`") {
      index += 1;
      continue;
    }
    let end = index + 1;
    while (text[end] === "`") end += 1;
    const marker = text.slice(index, end);
    const close = text.indexOf(marker, end);
    const lineEnd = text.indexOf("\n", end);
    const limit = marker.length >= 3 || lineEnd < 0 ? text.length : lineEnd;
    const rangeEnd = close >= 0 && close < limit ? close + marker.length : limit;
    ranges.push([index, rangeEnd]);
    index = Math.max(rangeEnd, end);
  }

  for (const tag of BLOCK_TAGS) {
    const open = new RegExp(`<${tag}\\b[^>]*>`, "gi");
    for (let match; (match = open.exec(text));) {
      const close = new RegExp(`</${tag}\\s*>`, "gi");
      close.lastIndex = open.lastIndex;
      const closing = close.exec(text);
      ranges.push([match.index, closing ? close.lastIndex : text.length]);
      if (!closing) break;
      open.lastIndex = close.lastIndex;
    }
  }
  return ranges;
}

function overlaps(ranges, start, end) {
  return ranges.some(([left, right]) => start < right && end > left);
}

export function inspectTelegramText(text) {
  if (typeof text !== "string" || !text) return { text, repairs: 0 };
  const protectedMarkup = protectedRanges(text);
  let repairs = 0;
  const boundary = /(?:[ \t]*\r?\n)*[ \t]*<br><br>[ \t\r\n]*(#{1,6} [^\r\n<]+)/gi;
  const repaired = text.replace(boundary, (match, heading, offset) => {
    if (overlaps(protectedMarkup, offset, offset + match.length)) return match;
    repairs += 1;
    return `\n\n${heading}`;
  });
  return { text: repaired, repairs };
}
