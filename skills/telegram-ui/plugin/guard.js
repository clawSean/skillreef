// Only repair a proven, exact rich-Markdown boundary. Ambiguous markup is inert.
export function inspectTelegramText(text) {
  if (typeof text !== "string" || !text) return { text, repairs: 0 };
  if (text.includes("`") || /<(?:pre|code|table|ul|ol|details)\b/i.test(text)) {
    return { text, repairs: 0 };
  }
  let repairs = 0;
  const repaired = text.replace(/<br><br>(#{1,6} [^\n<]+)/g, (_match, heading) => {
    repairs += 1;
    return `\n\n${heading}`;
  });
  return { text: repaired, repairs };
}
