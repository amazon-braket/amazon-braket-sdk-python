document.addEventListener("DOMContentLoaded", () => {
  const content = document.querySelector(
    '[role="main"] [itemprop="articleBody"]',
  );

  if (!content) {
    return;
  }

  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Copy as Markdown";
  button.style.cssText =
    "margin-bottom: 1em; padding: .4em .8em; cursor: pointer;";

  content.prepend(button);

  const convertToMarkdown = (node) => {
    if (node === button) {
      return "";
    }

    if (node.nodeType === Node.TEXT_NODE) {
      return node.nodeValue.replace(/\s+/g, " ");
    }

    if (node.nodeType !== Node.ELEMENT_NODE) {
      return "";
    }

    const tag = node.tagName.toLowerCase();

    if (
      node.matches(
        ".headerlink, .rst-footer-buttons, .copybutton, .highlight button",
      )
    ) {
      return "";
    }

    if (tag === "br") {
      return "\n";
    }

    const children = () =>
      Array.from(node.childNodes).map(convertToMarkdown).join("");

    if (/^h[1-6]$/.test(tag)) {
      const level = Number(tag[1]);
      return `\n\n${"#".repeat(level)} ${children().trim()}\n\n`;
    }

    if (tag === "pre") {
      const code = node.textContent.trim();
      const language = code.startsWith(">>>") ? "python" : "";

      return `\n\n\`\`\`${language}\n${code}\n\`\`\`\n\n`;
    }

    if (tag === "code") {
      return `\`${node.textContent.trim()}\``;
    }

    if (tag === "a") {
      const text = children().trim();
      const href = node.href;

      return href ? `[${text}](${href})` : text;
    }

    if (tag === "strong" || tag === "b") {
      return `**${children().trim()}**`;
    }

    if (tag === "em" || tag === "i") {
      return `*${children().trim()}*`;
    }

    if (tag === "ul" || tag === "ol") {
      const items = Array.from(node.children)
        .filter((child) => child.tagName.toLowerCase() === "li")
        .map((item, index) => {
          const prefix = tag === "ol" ? `${index + 1}. ` : "- ";
          const text = Array.from(item.childNodes)
            .map(convertToMarkdown)
            .join("")
            .trim();

          return `${prefix}${text}`;
        })
        .join("\n");

      return `\n\n${items}\n\n`;
    }

    if (tag === "p") {
      const text = children().trim();
      return text ? `\n\n${text}\n\n` : "";
    }

    return children();
  };

  button.addEventListener("click", async () => {
    try {
      const markdown = convertToMarkdown(content)
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n{3,}/g, "\n\n")
        .trim();

      await navigator.clipboard.writeText(markdown);

      button.textContent = "Copied!";

      setTimeout(() => {
        button.textContent = "Copy as Markdown";
      }, 1500);
    } catch {
      button.textContent = "Copy failed";

      setTimeout(() => {
        button.textContent = "Copy as Markdown";
      }, 1500);
    }
  });
});
