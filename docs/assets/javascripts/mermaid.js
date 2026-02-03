const initMermaid = async () => {
  if (typeof mermaid === "undefined") {
    setTimeout(initMermaid, 50);
    return;
  }

  const isDark = document.body.getAttribute("data-md-color-scheme") === "slate";
  const theme = isDark ? "base" : "default";

  const themeVariables = isDark ? {
    background: "#1E293B",
    primaryColor: "#334155",
    primaryTextColor: "#F1F5F9",
    primaryBorderColor: "#94A3B8",
    lineColor: "#CBD5E1",
    edgeColor: "#CBD5E1",
    defaultLinkColor: "#CBD5E1",
    secondaryColor: "#0F172A",
    tertiaryColor: "#1E293B"
  } : {};

  try {
    mermaid.initialize({
      startOnLoad: false,
      theme,
      themeVariables,
      flowchart: {
        useMaxWidth: false,
        htmlLabels: true
      },
      securityLevel: 'loose',
    });

    const nodes = document.querySelectorAll(".mermaid");
    if (nodes.length > 0) {
      await mermaid.run({ nodes });
    }
  } catch (err) {
    console.error(err);
  }
};

document.addEventListener("DOMContentLoaded", initMermaid);

const observer = new MutationObserver(mutations => {
  mutations.forEach(mutation => {
    if (mutation.type === "attributes" && mutation.attributeName === "data-md-color-scheme") {
      location.reload();
    }
  });
});

const body = document.querySelector("body");
if (body) {
  observer.observe(body, { attributes: true });
}
